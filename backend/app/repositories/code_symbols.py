from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.models.code_symbols import CodeSymbol
from app.repositories.database import Base, create_session_factory, create_sqlite_engine
from app.repositories.project_files import ProjectFileRecord
from app.repositories.projects import ProjectRecord


class CodeSymbolRecord(Base):
    __tablename__ = "code_symbols"

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
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    symbol_type: Mapped[str] = mapped_column(String, nullable=False)
    parent_symbol_id: Mapped[str | None] = mapped_column(
        ForeignKey("code_symbols.id", ondelete="CASCADE"),
        nullable=True,
    )
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    docstring: Mapped[str | None] = mapped_column(Text, nullable=True)


class CodeSymbolRepository:
    """Persist classes, functions, and methods discovered by AST analysis."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def save_many(self, symbols: list[CodeSymbol]) -> list[CodeSymbol]:
        self.initialize()
        with self._session_factory.begin() as session:
            session.add_all(
                [
                    CodeSymbolRecord(
                        id=str(symbol.id),
                        project_id=str(symbol.project_id),
                        file_id=str(symbol.file_id),
                        name=symbol.name,
                        symbol_type=symbol.symbol_type,
                        parent_symbol_id=(
                            str(symbol.parent_symbol_id)
                            if symbol.parent_symbol_id is not None
                            else None
                        ),
                        start_line=symbol.start_line,
                        end_line=symbol.end_line,
                        parameters=symbol.parameters,
                        docstring=symbol.docstring,
                    )
                    for symbol in symbols
                ]
            )
        return symbols

    def get_by_project_id(self, project_id: UUID) -> list[CodeSymbol]:
        return self._get_by(CodeSymbolRecord.project_id, project_id)

    def get_by_file_id(self, file_id: UUID) -> list[CodeSymbol]:
        return self._get_by(CodeSymbolRecord.file_id, file_id)

    def find_by_name(self, project_id: UUID, name: str) -> list[CodeSymbol]:
        self.initialize()
        with self._session_factory() as session:
            records = session.scalars(
                select(CodeSymbolRecord)
                .where(
                    CodeSymbolRecord.project_id == str(project_id),
                    CodeSymbolRecord.name == name,
                )
                .order_by(CodeSymbolRecord.file_id, CodeSymbolRecord.start_line)
            ).all()
        return [_to_code_symbol(record) for record in records]

    def delete_by_project_id(self, project_id: UUID) -> int:
        self.initialize()
        with self._session_factory.begin() as session:
            result = session.execute(
                delete(CodeSymbolRecord).where(
                    CodeSymbolRecord.project_id == str(project_id)
                )
            )
        return result.rowcount

    def _get_by(self, column, value: UUID) -> list[CodeSymbol]:
        self.initialize()
        with self._session_factory() as session:
            records = session.scalars(
                select(CodeSymbolRecord)
                .where(column == str(value))
                .order_by(CodeSymbolRecord.file_id, CodeSymbolRecord.start_line)
            ).all()
        return [_to_code_symbol(record) for record in records]


def _to_code_symbol(record: CodeSymbolRecord) -> CodeSymbol:
    return CodeSymbol(
        id=record.id,
        project_id=record.project_id,
        file_id=record.file_id,
        name=record.name,
        symbol_type=record.symbol_type,
        parent_symbol_id=record.parent_symbol_id,
        start_line=record.start_line,
        end_line=record.end_line,
        parameters=record.parameters,
        docstring=record.docstring,
    )


@lru_cache
def get_code_symbol_repository() -> CodeSymbolRepository:
    return CodeSymbolRepository(get_settings().database_path)
