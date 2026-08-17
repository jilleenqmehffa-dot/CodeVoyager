import os
from pathlib import Path

from app.core.exceptions import InvalidLocalProjectError
from app.models.projects import Project


def import_local_project(local_path: str | Path) -> Project:
    """Validate a local directory and construct its project metadata."""

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

    return Project(name=project_path.name, local_path=project_path)
