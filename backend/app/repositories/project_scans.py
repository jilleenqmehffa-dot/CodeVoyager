from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.models.project_scans import ProjectScan
from app.repositories.database import Base, create_session_factory, create_sqlite_engine
from app.repositories.projects import ProjectRecord


class ProjectScanRecord(Base):
    __tablename__ = "project_scans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectRecord.id, ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    frameworks: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    entrypoints: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class ProjectScanRepository:
    """Persist project-level scan summaries."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def save(self, scan: ProjectScan) -> ProjectScan:
        """Replace the current scan summary for a project."""

        self.initialize()
        with self._session_factory.begin() as session:
            session.execute(
                delete(ProjectScanRecord).where(
                    ProjectScanRecord.project_id == str(scan.project_id)
                )
            )
            session.add(
                ProjectScanRecord(
                    id=str(scan.id),
                    project_id=str(scan.project_id),
                    languages=scan.languages,
                    frameworks=scan.frameworks,
                    entrypoints=scan.entrypoints,
                    scanned_at=scan.scanned_at,
                )
            )
        return scan

    def get_by_project_id(self, project_id: UUID) -> ProjectScan | None:
        self.initialize()
        with self._session_factory() as session:
            record = session.scalar(
                select(ProjectScanRecord).where(
                    ProjectScanRecord.project_id == str(project_id)
                )
            )
        if record is None:
            return None

        scanned_at = record.scanned_at
        if scanned_at.tzinfo is None:
            scanned_at = scanned_at.replace(tzinfo=timezone.utc)
        return ProjectScan(
            id=record.id,
            project_id=record.project_id,
            languages=record.languages,
            frameworks=record.frameworks,
            entrypoints=record.entrypoints,
            scanned_at=scanned_at,
        )

    def delete_by_project_id(self, project_id: UUID) -> bool:
        self.initialize()
        with self._session_factory.begin() as session:
            result = session.execute(
                delete(ProjectScanRecord).where(
                    ProjectScanRecord.project_id == str(project_id)
                )
            )
        return result.rowcount > 0


@lru_cache
def get_project_scan_repository() -> ProjectScanRepository:
    return ProjectScanRepository(get_settings().database_path)
