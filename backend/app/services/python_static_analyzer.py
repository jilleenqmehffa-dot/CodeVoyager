import ast
import tokenize
from collections import defaultdict
from pathlib import Path
from uuid import UUID

from app.models.code_imports import CodeImport
from app.models.code_symbols import CodeSymbol, CodeSymbolType
from app.models.inheritance_relations import InheritanceRelation
from app.models.project_files import ProjectFile
from app.models.projects import Project
from app.models.static_analysis import (
    PythonAnalysisFailure,
    PythonStaticAnalysisResult,
)
from app.repositories.code_imports import CodeImportRepository
from app.repositories.code_symbols import CodeSymbolRepository
from app.repositories.inheritance_relations import InheritanceRelationRepository
from app.repositories.project_files import ProjectFileRepository


def analyze_project(
    project: Project,
    file_repository: ProjectFileRepository,
) -> PythonStaticAnalysisResult:
    """Analyze the Python source files recorded by the project scanner."""

    project_files = file_repository.get_python_source_by_project_id(project.id)
    result = PythonStaticAnalysisResult()

    for project_file in project_files:
        file_result = analyze_python_file(project, project_file)
        result.symbols.extend(file_result.symbols)
        result.imports.extend(file_result.imports)
        result.inheritance_relations.extend(file_result.inheritance_relations)
        result.failures.extend(file_result.failures)

    _resolve_local_parent_symbols(result)
    return result


def analyze_and_save_project(
    project: Project,
    file_repository: ProjectFileRepository,
    symbol_repository: CodeSymbolRepository,
    import_repository: CodeImportRepository,
    inheritance_repository: InheritanceRelationRepository,
) -> PythonStaticAnalysisResult:
    """Analyze a project and replace its previous Python analysis data."""

    result = analyze_project(project, file_repository)
    inheritance_repository.delete_by_project_id(project.id)
    import_repository.delete_by_project_id(project.id)
    symbol_repository.delete_by_project_id(project.id)
    symbol_repository.save_many(result.symbols)
    import_repository.save_many(result.imports)
    inheritance_repository.save_many(result.inheritance_relations)
    return result


def analyze_python_file(
    project: Project,
    project_file: ProjectFile,
) -> PythonStaticAnalysisResult:
    """Analyze one previously scanned Python source file."""

    try:
        source_path = _resolve_source_path(project.local_path, project_file.path)
        with tokenize.open(source_path) as source_file:
            source = source_file.read()
        tree = ast.parse(source, filename=project_file.path)
    except (OSError, SyntaxError, UnicodeError, ValueError) as exc:
        return PythonStaticAnalysisResult(
            failures=[
                PythonAnalysisFailure(
                    file_id=project_file.id,
                    path=project_file.path,
                    error=_format_analysis_error(exc),
                )
            ]
        )

    result = PythonStaticAnalysisResult()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            _add_class(project, project_file, node, result)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.symbols.append(
                _function_symbol(project, project_file, node, symbol_type="function")
            )

    result.imports = _extract_imports(project, project_file, tree)
    _resolve_local_parent_symbols(result)
    return result


def _add_class(
    project: Project,
    project_file: ProjectFile,
    node: ast.ClassDef,
    result: PythonStaticAnalysisResult,
) -> None:
    class_symbol = CodeSymbol(
        project_id=project.id,
        file_id=project_file.id,
        name=node.name,
        symbol_type="class",
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        docstring=ast.get_docstring(node),
    )
    result.symbols.append(class_symbol)

    for base in node.bases:
        parent_name = ast.unparse(base)
        if parent_name:
            result.inheritance_relations.append(
                InheritanceRelation(
                    project_id=project.id,
                    child_symbol_id=class_symbol.id,
                    parent_name=parent_name,
                )
            )

    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.symbols.append(
                _function_symbol(
                    project,
                    project_file,
                    child,
                    symbol_type="method",
                    parent_symbol_id=class_symbol.id,
                )
            )


def _function_symbol(
    project: Project,
    project_file: ProjectFile,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    symbol_type: CodeSymbolType,
    parent_symbol_id: UUID | None = None,
) -> CodeSymbol:
    return CodeSymbol(
        project_id=project.id,
        file_id=project_file.id,
        name=node.name,
        symbol_type=symbol_type,
        parent_symbol_id=parent_symbol_id,
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        parameters=_extract_parameters(node.args),
        docstring=ast.get_docstring(node),
    )


def _extract_parameters(arguments: ast.arguments) -> list[str]:
    parameters = [argument.arg for argument in arguments.posonlyargs]
    parameters.extend(argument.arg for argument in arguments.args)
    if arguments.vararg is not None:
        parameters.append(f"*{arguments.vararg.arg}")
    parameters.extend(argument.arg for argument in arguments.kwonlyargs)
    if arguments.kwarg is not None:
        parameters.append(f"**{arguments.kwarg.arg}")
    return parameters


def _extract_imports(
    project: Project,
    project_file: ProjectFile,
    tree: ast.AST,
) -> list[CodeImport]:
    imports: list[CodeImport] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                CodeImport(
                    project_id=project.id,
                    file_id=project_file.id,
                    module=alias.name,
                    alias=alias.asname,
                    line=node.lineno,
                )
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            module = f"{'.' * node.level}{node.module or ''}"
            imports.extend(
                CodeImport(
                    project_id=project.id,
                    file_id=project_file.id,
                    module=module,
                    imported_name=alias.name,
                    alias=alias.asname,
                    line=node.lineno,
                )
                for alias in node.names
            )
    return sorted(
        imports,
        key=lambda item: (item.line, item.module, item.imported_name or ""),
    )


def _resolve_local_parent_symbols(result: PythonStaticAnalysisResult) -> None:
    symbols_by_id = {symbol.id: symbol for symbol in result.symbols}
    classes_by_name: dict[str, list[CodeSymbol]] = defaultdict(list)
    for symbol in result.symbols:
        if symbol.symbol_type == "class":
            classes_by_name[symbol.name].append(symbol)

    for relation in result.inheritance_relations:
        child = symbols_by_id[relation.child_symbol_id]
        lookup_name = relation.parent_name.split("[", 1)[0].rsplit(".", 1)[-1]
        candidates = [
            symbol
            for symbol in classes_by_name.get(lookup_name, [])
            if symbol.id != child.id
        ]
        same_file_candidates = [
            symbol for symbol in candidates if symbol.file_id == child.file_id
        ]
        if len(same_file_candidates) == 1:
            relation.parent_symbol_id = same_file_candidates[0].id
        elif len(candidates) == 1:
            relation.parent_symbol_id = candidates[0].id


def _resolve_source_path(project_path: Path, relative_path: str) -> Path:
    root = project_path.expanduser().resolve(strict=True)
    source_path = (root / relative_path).resolve(strict=True)
    source_path.relative_to(root)
    if not source_path.is_file():
        raise ValueError(f"Source path is not a file: {relative_path}")
    return source_path


def _format_analysis_error(error: Exception) -> str:
    if isinstance(error, SyntaxError):
        location = f" at line {error.lineno}" if error.lineno else ""
        return f"SyntaxError{location}: {error.msg}"
    return f"{type(error).__name__}: {error}"
