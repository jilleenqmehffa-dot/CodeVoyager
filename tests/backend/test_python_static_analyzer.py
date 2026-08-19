from pathlib import Path
from textwrap import dedent

from app.models.project_files import ProjectFile, ProjectFileCategory
from app.models.projects import Project
from app.repositories.code_imports import CodeImportRepository
from app.repositories.code_symbols import CodeSymbolRepository
from app.repositories.inheritance_relations import InheritanceRelationRepository
from app.repositories.project_files import ProjectFileRepository
from app.repositories.projects import ProjectRepository
from app.services.python_static_analyzer import (
    analyze_and_save_project,
    analyze_project,
    analyze_python_file,
)


def test_analyze_python_file_extracts_symbols_imports_and_inheritance(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project"
    source_path = project_path / "service.py"
    project_path.mkdir()
    source_path.write_text(
        dedent(
            '''\
            import os, sys as system
            from app.services import Service as BaseService

            class Parent:
                pass

            class Child(Parent, BaseService):
                """Child documentation."""
                async def run(self, value, /, count=1, *items, enabled=True, **options):
                    """Run the service."""
                    return value

            def helper(name):
                """Help a caller."""
                return name
            '''
        ),
        encoding="utf-8",
    )
    project = Project(name="example", local_path=project_path)
    project_file = _python_file(project, "service.py")

    result = analyze_python_file(project, project_file)

    assert result.failures == []
    symbols = {symbol.name: symbol for symbol in result.symbols}
    assert symbols["Parent"].symbol_type == "class"
    assert symbols["Child"].symbol_type == "class"
    assert symbols["Child"].docstring == "Child documentation."
    assert symbols["Child"].start_line == 7
    assert symbols["Child"].end_line == 11
    assert symbols["run"].symbol_type == "method"
    assert symbols["run"].parent_symbol_id == symbols["Child"].id
    assert symbols["run"].parameters == [
        "self",
        "value",
        "count",
        "*items",
        "enabled",
        "**options",
    ]
    assert symbols["run"].docstring == "Run the service."
    assert symbols["run"].start_line == 9
    assert symbols["run"].end_line == 11
    assert symbols["helper"].symbol_type == "function"
    assert symbols["helper"].parent_symbol_id is None
    assert symbols["helper"].parameters == ["name"]

    imports = {
        (item.module, item.imported_name): item for item in result.imports
    }
    assert imports[("os", None)].alias is None
    assert imports[("sys", None)].alias == "system"
    assert imports[("app.services", "Service")].alias == "BaseService"
    assert imports[("app.services", "Service")].line == 2

    relations = {item.parent_name: item for item in result.inheritance_relations}
    assert relations["Parent"].child_symbol_id == symbols["Child"].id
    assert relations["Parent"].parent_symbol_id == symbols["Parent"].id
    assert relations["BaseService"].parent_symbol_id is None


def test_analyze_project_uses_scanned_python_sources_and_continues_on_error(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / "base.py").write_text("class Base:\n    pass\n", encoding="utf-8")
    (project_path / "child.py").write_text(
        "class Child(Base):\n    pass\n", encoding="utf-8"
    )
    (project_path / "broken.py").write_text(
        "def broken(:\n    pass\n", encoding="utf-8"
    )
    (project_path / "test_hidden.py").write_text(
        "def should_not_be_analyzed():\n    pass\n", encoding="utf-8"
    )

    project = Project(name="example", local_path=project_path)
    database_path = tmp_path / "analysis.db"
    project_repository = ProjectRepository(database_path)
    file_repository = ProjectFileRepository(database_path)
    project_repository.create(project)
    files = [
        _python_file(project, "base.py"),
        _python_file(project, "broken.py"),
        _python_file(project, "child.py"),
        _python_file(project, "test_hidden.py", category="test"),
        ProjectFile(
            project_id=project.id,
            path="frontend.ts",
            name="frontend.ts",
            file_type=".ts",
            language="TypeScript",
            category="source",
            is_directory=False,
        ),
    ]
    file_repository.save_many(project.id, files)

    result = analyze_project(project, file_repository)

    assert {symbol.name for symbol in result.symbols} == {"Base", "Child"}
    assert len(result.failures) == 1
    assert result.failures[0].path == "broken.py"
    assert result.failures[0].error.startswith("SyntaxError at line 1:")
    relation = result.inheritance_relations[0]
    base = next(symbol for symbol in result.symbols if symbol.name == "Base")
    assert relation.parent_name == "Base"
    assert relation.parent_symbol_id == base.id

    project_repository.engine.dispose()
    file_repository.engine.dispose()


def test_analyze_and_save_project_replaces_previous_analysis(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir()
    source_path = project_path / "module.py"
    source_path.write_text("def old_function():\n    pass\n", encoding="utf-8")

    project = Project(name="example", local_path=project_path)
    database_path = tmp_path / "analysis.db"
    project_repository = ProjectRepository(database_path)
    file_repository = ProjectFileRepository(database_path)
    symbol_repository = CodeSymbolRepository(database_path)
    import_repository = CodeImportRepository(database_path)
    inheritance_repository = InheritanceRelationRepository(database_path)
    project_repository.create(project)
    project_file = _python_file(project, "module.py")
    file_repository.save_many(project.id, [project_file])

    analyze_and_save_project(
        project,
        file_repository,
        symbol_repository,
        import_repository,
        inheritance_repository,
    )
    source_path.write_text(
        "import pathlib\n\ndef new_function(value):\n    return value\n",
        encoding="utf-8",
    )
    second = analyze_and_save_project(
        project,
        file_repository,
        symbol_repository,
        import_repository,
        inheritance_repository,
    )

    saved_symbols = symbol_repository.get_by_project_id(project.id)
    saved_imports = import_repository.get_by_project_id(project.id)
    assert [symbol.name for symbol in saved_symbols] == ["new_function"]
    assert saved_symbols[0].parameters == ["value"]
    assert [item.module for item in saved_imports] == ["pathlib"]
    assert len(saved_symbols) == len(second.symbols)
    assert symbol_repository.find_by_name(project.id, "old_function") == []

    for repository in (
        project_repository,
        file_repository,
        symbol_repository,
        import_repository,
        inheritance_repository,
    ):
        repository.engine.dispose()


def _python_file(
    project: Project,
    path: str,
    *,
    category: ProjectFileCategory = "source",
) -> ProjectFile:
    return ProjectFile(
        project_id=project.id,
        path=path,
        name=Path(path).name,
        file_type=".py",
        language="Python",
        category=category,
        is_directory=False,
    )
