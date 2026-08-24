from pathlib import Path

from app.models.code_symbols import CodeSymbol
from app.models.project_files import ProjectFile
from app.models.projects import Project
from app.repositories.code_symbols import CodeSymbolRepository
from app.repositories.project_files import ProjectFileRepository
from app.repositories.projects import ProjectRepository
from app.services.code_search import find_symbol, search_text


def _source_file(project: Project, path: str) -> ProjectFile:
    return ProjectFile(
        project_id=project.id,
        path=path,
        name=Path(path).name,
        file_type=".py",
        language="Python",
        category="source",
        is_directory=False,
    )


def _repositories(tmp_path: Path, project: Project):
    database_path = tmp_path / "search.db"
    ProjectRepository(database_path).create(project)
    return ProjectFileRepository(database_path), CodeSymbolRepository(database_path)


def test_search_text_returns_file_line_and_matching_code(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "main.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n", encoding="utf-8"
    )
    project = Project(name="Demo", local_path=project_root)
    file_repository, _ = _repositories(tmp_path, project)
    project_file = _source_file(project, "main.py")
    file_repository.save_many(project.id, [project_file])

    results = search_text(project, "FastAPI", file_repository)

    assert [(item.file_id, item.file_path, item.line_number, item.matched_text) for item in results] == [
        (project_file.id, "main.py", 1, "from fastapi import FastAPI"),
        (project_file.id, "main.py", 3, "app = FastAPI()"),
    ]


def test_search_text_returns_empty_for_missing_keyword(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "main.py").write_text("answer = 42\n", encoding="utf-8")
    project = Project(name="Demo", local_path=project_root)
    file_repository, _ = _repositories(tmp_path, project)
    file_repository.save_many(project.id, [_source_file(project, "main.py")])

    assert search_text(project, "not_here", file_repository) == []


def test_search_text_does_not_read_outside_project(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (tmp_path / "secret.py").write_text("PRIVATE_TOKEN\n", encoding="utf-8")
    project = Project(name="Demo", local_path=project_root)
    file_repository, _ = _repositories(tmp_path, project)
    file_repository.save_many(project.id, [_source_file(project, "../secret.py")])

    assert search_text(project, "PRIVATE_TOKEN", file_repository) == []


def test_unreadable_file_does_not_abort_text_search(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "valid.py").write_text("DATABASE_URL = 'sqlite://'\n", encoding="utf-8")
    project = Project(name="Demo", local_path=project_root)
    file_repository, _ = _repositories(tmp_path, project)
    missing = _source_file(project, "missing.py")
    valid = _source_file(project, "valid.py")
    file_repository.save_many(project.id, [missing, valid])

    results = search_text(project, "DATABASE_URL", file_repository)

    assert len(results) == 1
    assert results[0].file_id == valid.id


def test_find_symbol_returns_all_same_name_definitions(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    project = Project(name="Demo", local_path=project_root)
    file_repository, symbol_repository = _repositories(tmp_path, project)
    first_file = _source_file(project, "services/first.py")
    second_file = _source_file(project, "services/second.py")
    file_repository.save_many(project.id, [first_file, second_file])
    first_symbol = CodeSymbol(
        project_id=project.id, file_id=first_file.id, name="get_project",
        symbol_type="function", start_line=10, end_line=12,
    )
    second_symbol = CodeSymbol(
        project_id=project.id, file_id=second_file.id, name="get_project",
        symbol_type="method", start_line=20, end_line=24,
    )
    symbol_repository.save_many([first_symbol, second_symbol])

    results = find_symbol(
        project.id, "get_project", symbol_repository, file_repository
    )

    assert {item.symbol_id for item in results} == {first_symbol.id, second_symbol.id}
    assert {item.file_id for item in results} == {first_file.id, second_file.id}
    assert {item.file_path for item in results} == {
        "services/first.py", "services/second.py"
    }
    assert {(item.start_line, item.end_line) for item in results} == {(10, 12), (20, 24)}


def test_find_symbol_returns_empty_for_unknown_name(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    project = Project(name="Demo", local_path=project_root)
    file_repository, symbol_repository = _repositories(tmp_path, project)

    assert find_symbol(
        project.id, "UnknownSymbol", symbol_repository, file_repository
    ) == []
