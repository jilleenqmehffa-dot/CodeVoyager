import ast
import tokenize
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.models.code_symbols import CodeSymbol
from app.models.file_relationship import FileRelationship
from app.models.project_files import ProjectFile
from app.models.projects import Project
from app.repositories.code_symbols import CodeSymbolRepository
from app.repositories.project_files import ProjectFileRepository


@dataclass(frozen=True)
class _ParsedFile:
    project_file: ProjectFile
    module: str
    tree: ast.Module


def analyze_file_relationships(
    project: Project,
    file_repository: ProjectFileRepository,
    symbol_repository: CodeSymbolRepository,
) -> list[FileRelationship]:
    """Build code-graph relationships from scanned files and saved symbols."""

    parsed_files = _parse_project_files(project, file_repository)
    symbols = symbol_repository.get_by_project_id(project.id)
    symbols_by_location = {
        (symbol.file_id, symbol.name, symbol.start_line): symbol for symbol in symbols
    }
    symbols_by_name: dict[str, list[CodeSymbol]] = defaultdict(list)
    for symbol in symbols:
        symbols_by_name[symbol.name].append(symbol)

    files_by_module = {item.module: item.project_file for item in parsed_files}
    relationships: list[FileRelationship] = []
    for parsed_file in parsed_files:
        relationships.extend(
            _import_relationships(project.id, parsed_file, files_by_module)
        )
        visitor = _SymbolRelationshipVisitor(
            project_id=project.id,
            parsed_file=parsed_file,
            symbols_by_location=symbols_by_location,
            symbols_by_name=symbols_by_name,
        )
        visitor.visit(parsed_file.tree)
        relationships.extend(visitor.relationships)

    return _deduplicate(relationships)


def _parse_project_files(
    project: Project,
    file_repository: ProjectFileRepository,
) -> list[_ParsedFile]:
    parsed_files: list[_ParsedFile] = []
    root = project.local_path.expanduser().resolve(strict=True)
    for project_file in file_repository.get_python_source_by_project_id(project.id):
        try:
            path = (root / project_file.path).resolve(strict=True)
            path.relative_to(root)
            with tokenize.open(path) as source_file:
                tree = ast.parse(source_file.read(), filename=project_file.path)
        except (OSError, SyntaxError, UnicodeError, ValueError):
            continue
        parsed_files.append(
            _ParsedFile(
                project_file=project_file,
                module=_module_name(project_file.path),
                tree=tree,
            )
        )
    return parsed_files


def _module_name(path: str) -> str:
    module_path = Path(path).with_suffix("")
    parts = list(module_path.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _import_relationships(
    project_id: UUID,
    parsed_file: _ParsedFile,
    files_by_module: dict[str, ProjectFile],
) -> list[FileRelationship]:
    relationships: list[FileRelationship] = []
    for node in ast.walk(parsed_file.tree):
        if isinstance(node, ast.Import):
            imported_modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported_modules = [
                _absolute_import_module(parsed_file.module, node)
            ]
        else:
            continue

        for target_module in imported_modules:
            if not target_module:
                continue
            target_file = _find_module_file(target_module, files_by_module)
            relationships.append(
                FileRelationship(
                    project_id=project_id,
                    relationship_type="import",
                    source_type="module",
                    target_type="module",
                    source_file_id=parsed_file.project_file.id,
                    target_file_id=target_file.id if target_file else None,
                    source_module=parsed_file.module,
                    target_module=target_module,
                    line=node.lineno,
                    column=node.col_offset,
                )
            )
            if target_file is not None:
                relationships.append(
                    FileRelationship(
                        project_id=project_id,
                        relationship_type="import",
                        source_type="file",
                        target_type="file",
                        source_file_id=parsed_file.project_file.id,
                        target_file_id=target_file.id,
                        line=node.lineno,
                        column=node.col_offset,
                    )
                )
    return relationships


def _absolute_import_module(current_module: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package = current_module.split(".")[:-1]
    keep = max(0, len(package) - node.level + 1)
    prefix = package[:keep]
    if node.module:
        prefix.extend(node.module.split("."))
    return ".".join(prefix)


def _find_module_file(
    module: str,
    files_by_module: dict[str, ProjectFile],
) -> ProjectFile | None:
    candidate = module
    while candidate:
        if candidate in files_by_module:
            return files_by_module[candidate]
        candidate = candidate.rpartition(".")[0]
    return None


class _SymbolRelationshipVisitor(ast.NodeVisitor):
    def __init__(
        self,
        *,
        project_id: UUID,
        parsed_file: _ParsedFile,
        symbols_by_location: dict[tuple[UUID, str, int], CodeSymbol],
        symbols_by_name: dict[str, list[CodeSymbol]],
    ) -> None:
        self.project_id = project_id
        self.parsed_file = parsed_file
        self.symbols_by_location = symbols_by_location
        self.symbols_by_name = symbols_by_name
        self.relationships: list[FileRelationship] = []
        self._symbol_stack: list[CodeSymbol] = []
        self._excluded_reference_nodes: set[int] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        symbol = self._symbol(node)
        if symbol is None:
            self.generic_visit(node)
            return
        for base in node.bases:
            self._excluded_reference_nodes.update(id(item) for item in ast.walk(base))
            self._add_symbol_relationship("inheritance", symbol, base, node.lineno)
        self._symbol_stack.append(symbol)
        self.generic_visit(node)
        self._symbol_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        symbol = self._symbol(node)
        if symbol is None:
            self.generic_visit(node)
            return
        self._symbol_stack.append(symbol)
        self.generic_visit(node)
        self._symbol_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if self._symbol_stack and self._symbol_stack[-1].symbol_type in {
            "function",
            "method",
        }:
            self._excluded_reference_nodes.update(id(item) for item in ast.walk(node.func))
            self._add_symbol_relationship(
                "call", self._symbol_stack[-1], node.func, node.lineno
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        self._visit_reference(node, node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self._visit_reference(node, node.attr)
        self.generic_visit(node)

    def _visit_reference(self, node: ast.expr, name: str) -> None:
        if not self._symbol_stack or id(node) in self._excluded_reference_nodes:
            return
        target = self._resolve_symbol(name)
        source = self._symbol_stack[-1]
        if target is None or target.id == source.id:
            return
        self.relationships.append(
            self._relationship("reference", source, target, name, node.lineno, node.col_offset)
        )

    def _add_symbol_relationship(
        self,
        relationship_type: str,
        source: CodeSymbol,
        target_node: ast.expr,
        line: int,
    ) -> None:
        name = _expression_name(target_node)
        if not name:
            return
        target = self._resolve_symbol(name.rsplit(".", 1)[-1])
        self.relationships.append(
            self._relationship(
                relationship_type,
                source,
                target,
                name,
                line,
                target_node.col_offset,
            )
        )

    def _relationship(
        self,
        relationship_type: str,
        source: CodeSymbol,
        target: CodeSymbol | None,
        target_name: str,
        line: int,
        column: int,
    ) -> FileRelationship:
        return FileRelationship(
            project_id=self.project_id,
            relationship_type=relationship_type,
            source_type=_entity_type(source),
            target_type=_entity_type(target) if target else _fallback_target_type(relationship_type),
            source_file_id=source.file_id,
            target_file_id=target.file_id if target else None,
            source_symbol_id=source.id,
            target_symbol_id=target.id if target else None,
            target_name=target_name,
            line=line,
            column=column,
        )

    def _symbol(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> CodeSymbol | None:
        return self.symbols_by_location.get(
            (self.parsed_file.project_file.id, node.name, node.lineno)
        )

    def _resolve_symbol(self, name: str) -> CodeSymbol | None:
        candidates = self.symbols_by_name.get(name, [])
        same_file = [
            symbol
            for symbol in candidates
            if symbol.file_id == self.parsed_file.project_file.id
        ]
        if len(same_file) == 1:
            return same_file[0]
        if len(candidates) == 1:
            return candidates[0]
        return None


def _expression_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _expression_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Subscript):
        return _expression_name(node.value)
    return None


def _entity_type(symbol: CodeSymbol) -> str:
    return "class" if symbol.symbol_type == "class" else "function"


def _fallback_target_type(relationship_type: str) -> str:
    return "class" if relationship_type == "inheritance" else "function"


def _deduplicate(relationships: list[FileRelationship]) -> list[FileRelationship]:
    seen: set[tuple[object, ...]] = set()
    unique: list[FileRelationship] = []
    for relationship in relationships:
        key = (
            relationship.relationship_type,
            relationship.source_type,
            relationship.target_type,
            relationship.source_file_id,
            relationship.target_file_id,
            relationship.source_symbol_id,
            relationship.target_symbol_id,
            relationship.source_module,
            relationship.target_module,
            relationship.target_name,
            relationship.line,
            relationship.column,
        )
        if key not in seen:
            seen.add(key)
            unique.append(relationship)
    return unique
