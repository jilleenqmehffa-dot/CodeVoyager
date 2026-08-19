from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.models.project_files import ProjectFile, ProjectFileCategory
from app.repositories.database import Base, create_session_factory, create_sqlite_engine
from app.repositories.projects import ProjectRecord


class ProjectFileRecord(Base):
    __tablename__ = "project_files"
    __table_args__ = (UniqueConstraint("project_id", "path"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectRecord.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    is_directory: Mapped[bool] = mapped_column(Boolean, nullable=False)


class ProjectFileRepository:
    """Persist files and directories discovered by a project scan."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def save_many(
        self,
        project_id: UUID,
        files: list[ProjectFile],
    ) -> list[ProjectFile]:
        """Replace all persisted filesystem entries for a project."""

        self.initialize()
        with self._session_factory.begin() as session:
            session.execute(
                delete(ProjectFileRecord).where(
                    ProjectFileRecord.project_id == str(project_id)
                )
            )
            session.add_all(
                [
                    ProjectFileRecord(
                        id=str(file.id),
                        project_id=str(file.project_id),
                        path=file.path,
                        name=file.name,
                        file_type=file.file_type,
                        language=file.language,
                        category=file.category,
                        is_directory=file.is_directory,
                    )
                    for file in files
                ]
            )
        return files

    def get_by_project_id(self, project_id: UUID) -> list[ProjectFile]:
        self.initialize()
        with self._session_factory() as session:
            records = session.scalars(
                select(ProjectFileRecord)
                .where(ProjectFileRecord.project_id == str(project_id))
                .order_by(ProjectFileRecord.path)
            ).all()
        return [
            ProjectFile(
                id=record.id,
                project_id=record.project_id,
                path=record.path,
                name=record.name,
                file_type=record.file_type,
                language=record.language,
                category=record.category,
                is_directory=record.is_directory,
            )
            for record in records
        ]

    def get_python_source_by_project_id(
        self,
        project_id: UUID,
    ) -> list[ProjectFile]:
        """Return scanned Python source files eligible for static analysis."""

        self.initialize()
        with self._session_factory() as session:
            records = session.scalars(
                select(ProjectFileRecord)
                .where(
                    ProjectFileRecord.project_id == str(project_id),
                    ProjectFileRecord.language == "Python",
                    ProjectFileRecord.category == "source",
                    ProjectFileRecord.is_directory.is_(False),
                )
                .order_by(ProjectFileRecord.path)
            ).all()
        return [
            ProjectFile(
                id=record.id,
                project_id=record.project_id,
                path=record.path,
                name=record.name,
                file_type=record.file_type,
                language=record.language,
                category=record.category,
                is_directory=record.is_directory,
            )
            for record in records
        ]

    def delete_by_project_id(self, project_id: UUID) -> int:
        self.initialize()
        with self._session_factory.begin() as session:
            result = session.execute(
                delete(ProjectFileRecord).where(
                    ProjectFileRecord.project_id == str(project_id)
                )
            )
        return result.rowcount


@lru_cache
def get_project_file_repository() -> ProjectFileRepository:
    return ProjectFileRepository(get_settings().database_path)
