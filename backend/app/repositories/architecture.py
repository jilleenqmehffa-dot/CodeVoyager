from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.models.architecture import ArchitectureEdge, ArchitectureMap, ArchitectureNode
from app.repositories.code_symbols import CodeSymbolRecord
from app.repositories.database import Base, create_session_factory, create_sqlite_engine
from app.repositories.project_files import ProjectFileRecord
from app.repositories.projects import ProjectRecord


class ArchitectureNodeRecord(Base):
    __tablename__ = "architecture_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectRecord.id, ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    node_type: Mapped[str] = mapped_column(String, nullable=False)
    file_id: Mapped[str | None] = mapped_column(
        ForeignKey(ProjectFileRecord.id, ondelete="SET NULL"), nullable=True
    )
    symbol_id: Mapped[str | None] = mapped_column(
        ForeignKey(CodeSymbolRecord.id, ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_node_id: Mapped[str | None] = mapped_column(
        ForeignKey("architecture_nodes.id", ondelete="CASCADE"), nullable=True
    )


class ArchitectureEdgeRecord(Base):
    __tablename__ = "architecture_edges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey(ProjectRecord.id, ondelete="CASCADE"), nullable=False, index=True
    )
    source_node_id: Mapped[str] = mapped_column(
        ForeignKey(ArchitectureNodeRecord.id, ondelete="CASCADE"), nullable=False
    )
    target_node_id: Mapped[str] = mapped_column(
        ForeignKey(ArchitectureNodeRecord.id, ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String, nullable=False)


class ArchitectureRepository:
    """Atomically replace and query a project's architecture graph."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.engine: Engine = create_sqlite_engine(self.database_path)
        self._session_factory = create_session_factory(self.engine)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self.engine)

    def save(self, architecture: ArchitectureMap) -> ArchitectureMap:
        self._validate_graph(architecture)
        self.initialize()
        project_id = str(architecture.project_id)
        with self._session_factory.begin() as session:
            session.execute(
                delete(ArchitectureEdgeRecord).where(
                    ArchitectureEdgeRecord.project_id == project_id
                )
            )
            session.execute(
                delete(ArchitectureNodeRecord).where(
                    ArchitectureNodeRecord.project_id == project_id
                )
            )
            nodes = _parents_before_children(architecture.nodes)
            session.add_all([_node_record(node) for node in nodes])
            session.flush()
            session.add_all([_edge_record(edge) for edge in architecture.edges])
        return architecture

    def get_by_project_id(self, project_id: UUID) -> ArchitectureMap | None:
        self.initialize()
        value = str(project_id)
        with self._session_factory() as session:
            node_records = session.scalars(
                select(ArchitectureNodeRecord)
                .where(ArchitectureNodeRecord.project_id == value)
                .order_by(ArchitectureNodeRecord.name, ArchitectureNodeRecord.id)
            ).all()
            if not node_records:
                return None
            edge_records = session.scalars(
                select(ArchitectureEdgeRecord)
                .where(ArchitectureEdgeRecord.project_id == value)
                .order_by(ArchitectureEdgeRecord.id)
            ).all()
        return ArchitectureMap(
            project_id=project_id,
            nodes=[_to_node(record) for record in node_records],
            edges=[_to_edge(record) for record in edge_records],
        )

    @staticmethod
    def _validate_graph(architecture: ArchitectureMap) -> None:
        node_ids = {node.id for node in architecture.nodes}
        if len(node_ids) != len(architecture.nodes):
            raise ValueError("architecture node IDs must be unique")
        for node in architecture.nodes:
            if node.project_id != architecture.project_id:
                raise ValueError("all architecture nodes must belong to the map project")
            if node.parent_node_id is not None and node.parent_node_id not in node_ids:
                raise ValueError("parent_node_id must reference a node in the map")
        for edge in architecture.edges:
            if edge.project_id != architecture.project_id:
                raise ValueError("all architecture edges must belong to the map project")
            if edge.source_node_id not in node_ids or edge.target_node_id not in node_ids:
                raise ValueError("architecture edges must reference nodes in the map")


def _node_record(node: ArchitectureNode) -> ArchitectureNodeRecord:
    return ArchitectureNodeRecord(
        id=str(node.id), project_id=str(node.project_id), name=node.name,
        node_type=node.node_type,
        file_id=str(node.file_id) if node.file_id else None,
        symbol_id=str(node.symbol_id) if node.symbol_id else None,
        description=node.description,
        parent_node_id=str(node.parent_node_id) if node.parent_node_id else None,
    )


def _parents_before_children(nodes: list[ArchitectureNode]) -> list[ArchitectureNode]:
    """Order arbitrary valid trees so SQLite can enforce the self foreign key."""
    remaining = {node.id: node for node in nodes}
    ordered: list[ArchitectureNode] = []
    inserted: set[UUID] = set()
    while remaining:
        ready = [
            node
            for node in remaining.values()
            if node.parent_node_id is None or node.parent_node_id in inserted
        ]
        if not ready:
            raise ValueError("architecture parent relationships must not contain cycles")
        for node in ready:
            ordered.append(node)
            inserted.add(node.id)
            del remaining[node.id]
    return ordered


def _edge_record(edge: ArchitectureEdge) -> ArchitectureEdgeRecord:
    return ArchitectureEdgeRecord(
        id=str(edge.id), project_id=str(edge.project_id),
        source_node_id=str(edge.source_node_id),
        target_node_id=str(edge.target_node_id), relation_type=edge.relation_type,
    )


def _to_node(record: ArchitectureNodeRecord) -> ArchitectureNode:
    return ArchitectureNode(
        id=record.id, project_id=record.project_id, name=record.name,
        node_type=record.node_type, file_id=record.file_id,
        symbol_id=record.symbol_id, description=record.description,
        parent_node_id=record.parent_node_id,
    )


def _to_edge(record: ArchitectureEdgeRecord) -> ArchitectureEdge:
    return ArchitectureEdge(
        id=record.id, project_id=record.project_id,
        source_node_id=record.source_node_id, target_node_id=record.target_node_id,
        relation_type=record.relation_type,
    )


@lru_cache
def get_architecture_repository() -> ArchitectureRepository:
    return ArchitectureRepository(get_settings().database_path)
