from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import ForeignKey, String, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.models.inheritance_relations import InheritanceRelation
from app.repositories.code_symbols import CodeSymbolRecord
from app.repositories.database import Base, create_session_factory, create_sqlite_engine
from app.repositories.projects import ProjectRecord


class InheritanceRelationRecord(Base):
    __tablename__ = "inheritance_relations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectRecord.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_symbol_id: Mapped[str] = mapped_column(
        ForeignKey(CodeSymbolRecord.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_symbol_id: Mapped[str | None] = mapped_column(
        ForeignKey(CodeSymbolRecord.id, ondelete="SET NULL"),
        nullable=True,
    )


class InheritanceRelationRepository:
    """Persist class inheritance declarations."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def save_many(
        self,
        relations: list[InheritanceRelation],
    ) -> list[InheritanceRelation]:
        self.initialize()
        with self._session_factory.begin() as session:
            session.add_all(
                [
                    InheritanceRelationRecord(
                        id=str(relation.id),
                        project_id=str(relation.project_id),
                        child_symbol_id=str(relation.child_symbol_id),
                        parent_name=relation.parent_name,
                        parent_symbol_id=(
                            str(relation.parent_symbol_id)
                            if relation.parent_symbol_id is not None
                            else None
                        ),
                    )
                    for relation in relations
                ]
            )
        return relations

    def get_by_project_id(self, project_id: UUID) -> list[InheritanceRelation]:
        self.initialize()
        with self._session_factory() as session:
            records = session.scalars(
                select(InheritanceRelationRecord)
                .where(InheritanceRelationRecord.project_id == str(project_id))
                .order_by(InheritanceRelationRecord.child_symbol_id)
            ).all()
        return [_to_inheritance_relation(record) for record in records]

    def delete_by_project_id(self, project_id: UUID) -> int:
        self.initialize()
        with self._session_factory.begin() as session:
            result = session.execute(
                delete(InheritanceRelationRecord).where(
                    InheritanceRelationRecord.project_id == str(project_id)
                )
            )
        return result.rowcount


def _to_inheritance_relation(
    record: InheritanceRelationRecord,
) -> InheritanceRelation:
    return InheritanceRelation(
        id=record.id,
        project_id=record.project_id,
        child_symbol_id=record.child_symbol_id,
        parent_name=record.parent_name,
        parent_symbol_id=record.parent_symbol_id,
    )


@lru_cache
def get_inheritance_relation_repository() -> InheritanceRelationRepository:
    return InheritanceRelationRepository(get_settings().database_path)
