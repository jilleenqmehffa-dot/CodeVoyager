from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, Text, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.models.project_overview import ProjectOverview
from app.repositories.database import Base, create_session_factory, create_sqlite_engine
from app.repositories.projects import ProjectRecord


class ProjectOverviewRecord(Base):
    __tablename__ = "project_overviews"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectRecord.id, ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[str | None] = mapped_column(String, nullable=True)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    dependencies: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    core_modules: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    entrypoints: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    configuration_systems: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    databases: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    apis: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    test_methods: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    run_commands: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class ProjectOverviewRepository:
    """Persist and query generated project overviews."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def save(self, overview: ProjectOverview) -> ProjectOverview:
        """Replace the current overview for a project."""

        self.initialize()
        with self._session_factory.begin() as session:
            session.execute(
                delete(ProjectOverviewRecord).where(
                    ProjectOverviewRecord.project_id == str(overview.project_id)
                )
            )
            session.add(
                ProjectOverviewRecord(
                    id=str(overview.id),
                    project_id=str(overview.project_id),
                    purpose=overview.purpose,
                    project_type=overview.project_type,
                    tech_stack=overview.tech_stack,
                    languages=overview.languages,
                    dependencies=overview.dependencies,
                    core_modules=overview.core_modules,
                    entrypoints=overview.entrypoints,
                    configuration_systems=overview.configuration_systems,
                    databases=overview.databases,
                    apis=overview.apis,
                    test_methods=overview.test_methods,
                    run_commands=overview.run_commands,
                )
            )
        return overview

    def get_by_project_id(self, project_id: UUID) -> ProjectOverview | None:
        """Query the overview belonging to a project."""

        self.initialize()
        with self._session_factory() as session:
            record = session.scalar(
                select(ProjectOverviewRecord).where(
                    ProjectOverviewRecord.project_id == str(project_id)
                )
            )
        if record is None:
            return None
        return _to_project_overview(record)


def _to_project_overview(record: ProjectOverviewRecord) -> ProjectOverview:
    return ProjectOverview(
        id=record.id,
        project_id=record.project_id,
        purpose=record.purpose,
        project_type=record.project_type,
        tech_stack=record.tech_stack,
        languages=record.languages,
        dependencies=record.dependencies,
        core_modules=record.core_modules,
        entrypoints=record.entrypoints,
        configuration_systems=record.configuration_systems,
        databases=record.databases,
        apis=record.apis,
        test_methods=record.test_methods,
        run_commands=record.run_commands,
    )


@lru_cache
def get_project_overview_repository() -> ProjectOverviewRepository:
    return ProjectOverviewRepository(get_settings().database_path)
