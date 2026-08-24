import asyncio
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.exceptions import FileReadError
from app.models.project_files import ProjectFile
from app.models.projects import Project
from app.repositories.project_files import ProjectFileRepository
from app.repositories.projects import ProjectRepository
from app.routers.projects import get_project_file_content_route
from app.services.read_file import read_file


def _project_file(project: Project, path: str, *, is_directory: bool = False) -> ProjectFile:
    return ProjectFile(
        project_id=project.id,
        path=path,
        name=Path(path).name,
        file_type=".py",
        language="Python",
        category="source",
        is_directory=is_directory,
    )


def test_read_file_returns_source_as_string(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("print('hello')\n", encoding="utf-8")
    project = Project(name="Demo", local_path=tmp_path)

    content = read_file(project.local_path, _project_file(project, "app.py"))

    assert content == "print('hello')\n"


def test_read_file_rejects_paths_outside_project(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside = tmp_path / "secret.py"
    outside.write_text("secret = True", encoding="utf-8")
    project = Project(name="Demo", local_path=project_root)

    with pytest.raises(FileReadError, match="Unable to read file"):
        read_file(project.local_path, _project_file(project, "../secret.py"))


def test_project_file_repository_get_is_scoped_to_project(tmp_path: Path) -> None:
    database_path = tmp_path / "files.db"
    first = Project(name="First", local_path=tmp_path / "first")
    second = Project(name="Second", local_path=tmp_path / "second")
    project_repository = ProjectRepository(database_path)
    project_repository.create(first)
    project_repository.create(second)
    project_file = _project_file(first, "app.py")
    repository = ProjectFileRepository(database_path)
    repository.save_many(first.id, [project_file])

    assert repository.get(first.id, project_file.id) == project_file
    assert repository.get(second.id, project_file.id) is None
    assert repository.get(first.id, uuid4()) is None


def test_file_content_route_returns_path_metadata_and_content(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("answer = 42\n", encoding="utf-8")
    database_path = tmp_path / "route.db"
    project = Project(name="Demo", local_path=tmp_path)
    project_repository = ProjectRepository(database_path)
    project_repository.create(project)
    project_file = _project_file(project, "main.py")
    file_repository = ProjectFileRepository(database_path)
    file_repository.save_many(project.id, [project_file])

    response = asyncio.run(
        get_project_file_content_route(
            project.id, project_file.id, project_repository, file_repository
        )
    )

    assert response.path == "main.py"
    assert response.language == "Python"
    assert response.content == "answer = 42\n"
