import os
from pathlib import Path

from app.core.exceptions import InvalidLocalProjectError
from app.models.projects import Project
from app.repositories.projects import ProjectRepository


def import_local_project(
    name: str,
    local_path: str | Path,
    repository: ProjectRepository,
) -> Project:
    """Validate a local directory and persist its project metadata."""

    project_name = name.strip()
    if not project_name:
        raise InvalidLocalProjectError("Project name cannot be empty")

    raw_path = str(local_path).strip()
    if not raw_path:
        raise InvalidLocalProjectError("Local project path cannot be empty")

    try:
        project_path = Path(raw_path).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InvalidLocalProjectError(
            f"Local project path does not exist: {raw_path}"
        ) from exc

    if not project_path.is_dir():
        raise InvalidLocalProjectError(
            f"Local project path is not a directory: {project_path}"
        )
    if not os.access(project_path, os.R_OK | os.X_OK):
        raise InvalidLocalProjectError(
            f"Local project directory is not accessible: {project_path}"
        )
    if not project_path.name:
        raise InvalidLocalProjectError("Filesystem root cannot be imported as a project")

    project = Project(name=project_name, local_path=project_path)
    return repository.create(project)
