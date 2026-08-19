from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import String, delete
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.core.exceptions import ProjectAlreadyExistsError
from app.models.projects import Project
from app.repositories.database import Base, create_session_factory, create_sqlite_engine


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    local_path: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class ProjectRepository:
    """Persist and retrieve project metadata with SQLAlchemy and SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def create(self, project: Project) -> Project:
        self.initialize()
        try:
            with self._session_factory.begin() as session:
                session.add(
                    ProjectRecord(
                        id=str(project.id),
                        name=project.name,
                        local_path=str(project.local_path),
                    )
                )
        except IntegrityError as exc:
            raise ProjectAlreadyExistsError(
                f"Project has already been imported: {project.local_path}"
            ) from exc
        return project

    def get(self, project_id: UUID) -> Project | None:
        self.initialize()
        with self._session_factory() as session:
            record = session.get(ProjectRecord, str(project_id))
        if record is None:
            return None
        return Project(
            id=record.id,
            name=record.name,
            local_path=record.local_path,
        )

    def delete(self, project_id: UUID) -> bool:
        """Delete a project by ID and report whether it existed."""

        self.initialize()
        with self._session_factory.begin() as session:
            result = session.execute(
                delete(ProjectRecord).where(ProjectRecord.id == str(project_id))
            )
        return result.rowcount > 0


@lru_cache
def get_project_repository() -> ProjectRepository:
    return ProjectRepository(get_settings().database_path)
