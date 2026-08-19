from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.models.code_imports import CodeImport
from app.repositories.database import Base, create_session_factory, create_sqlite_engine
from app.repositories.project_files import ProjectFileRecord
from app.repositories.projects import ProjectRecord


class CodeImportRecord(Base):
    __tablename__ = "code_imports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectRecord.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectFileRecord.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[str] = mapped_column(String, nullable=False)
    imported_name: Mapped[str | None] = mapped_column(String, nullable=True)
    alias: Mapped[str | None] = mapped_column(String, nullable=True)
    line: Mapped[int] = mapped_column(Integer, nullable=False)


class CodeImportRepository:
    """Persist Python import declarations."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def save_many(self, imports: list[CodeImport]) -> list[CodeImport]:
        self.initialize()
        with self._session_factory.begin() as session:
            session.add_all(
                [
                    CodeImportRecord(
                        id=str(code_import.id),
                        project_id=str(code_import.project_id),
                        file_id=str(code_import.file_id),
                        module=code_import.module,
                        imported_name=code_import.imported_name,
                        alias=code_import.alias,
                        line=code_import.line,
                    )
                    for code_import in imports
                ]
            )
        return imports

    def get_by_project_id(self, project_id: UUID) -> list[CodeImport]:
        return self._get_by(CodeImportRecord.project_id, project_id)

    def get_by_file_id(self, file_id: UUID) -> list[CodeImport]:
        return self._get_by(CodeImportRecord.file_id, file_id)

    def delete_by_project_id(self, project_id: UUID) -> int:
        self.initialize()
        with self._session_factory.begin() as session:
            result = session.execute(
                delete(CodeImportRecord).where(
                    CodeImportRecord.project_id == str(project_id)
                )
            )
        return result.rowcount

    def _get_by(self, column, value: UUID) -> list[CodeImport]:
        self.initialize()
        with self._session_factory() as session:
            records = session.scalars(
                select(CodeImportRecord)
                .where(column == str(value))
                .order_by(CodeImportRecord.file_id, CodeImportRecord.line)
            ).all()
        return [_to_code_import(record) for record in records]


def _to_code_import(record: CodeImportRecord) -> CodeImport:
    return CodeImport(
        id=record.id,
        project_id=record.project_id,
        file_id=record.file_id,
        module=record.module,
        imported_name=record.imported_name,
        alias=record.alias,
        line=record.line,
    )


@lru_cache
def get_code_import_repository() -> CodeImportRepository:
    return CodeImportRepository(get_settings().database_path)
