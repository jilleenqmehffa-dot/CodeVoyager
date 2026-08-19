import sqlite3
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from app.config import get_settings
from app.core.exceptions import ProjectAlreadyExistsError
from app.models.projects import Project


class ProjectRepository:
    """Persist and retrieve project metadata in SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    local_path TEXT NOT NULL UNIQUE
                )
                """
            )

    def create(self, project: Project) -> Project:
        self.initialize()
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO projects (id, name, local_path) VALUES (?, ?, ?)",
                    (str(project.id), project.name, str(project.local_path)),
                )
        except sqlite3.IntegrityError as exc:
            raise ProjectAlreadyExistsError(
                f"Project has already been imported: {project.local_path}"
            ) from exc
        return project

    def get(self, project_id: UUID) -> Project | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name, local_path FROM projects WHERE id = ?",
                (str(project_id),),
            ).fetchone()
        if row is None:
            return None
        return Project(id=row["id"], name=row["name"], local_path=row["local_path"])

    def delete(self, project_id: UUID) -> bool:
        """Delete a project by ID and report whether it existed."""

        self.initialize()
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM projects WHERE id = ?",
                (str(project_id),),
            )
        return cursor.rowcount > 0

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


@lru_cache
def get_project_repository() -> ProjectRepository:
    return ProjectRepository(get_settings().database_path)
