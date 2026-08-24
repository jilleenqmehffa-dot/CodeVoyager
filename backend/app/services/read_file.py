from pathlib import Path

from app.core.exceptions import FileReadError
from app.models.project_files import ProjectFile

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024


def read_file(project_path: Path, project_file: ProjectFile) -> str:
    """Safely read a scanned project file as a UTF-8 string."""

    if project_file.is_directory:
        raise FileReadError(f"Cannot read a directory: {project_file.path}")

    try:
        root = project_path.expanduser().resolve(strict=True)
        target = (root / project_file.path).resolve(strict=True)
        target.relative_to(root)
        if not target.is_file():
            raise FileReadError(f"Path is not a file: {project_file.path}")
        if target.stat().st_size > MAX_FILE_SIZE_BYTES:
            raise FileReadError(
                f"File is larger than {MAX_FILE_SIZE_BYTES} bytes: {project_file.path}"
            )
        return target.read_text(encoding="utf-8")
    except FileReadError:
        raise
    except (OSError, UnicodeError, ValueError) as exc:
        raise FileReadError(f"Unable to read file: {project_file.path}") from exc
