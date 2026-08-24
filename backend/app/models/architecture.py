from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

ArchitectureNodeType = Literal[
    "project",
    "api",
    "service",
    "database",
    "core",
    "module",
]
ArchitectureRelationType = Literal[
    "contains",
    "calls",
    "accesses",
    "imports",
    "depends_on",
]


class ArchitectureNode(BaseModel):
    """A renderable entity in a project's architecture graph."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    name: str = Field(min_length=1, max_length=255)
    node_type: ArchitectureNodeType
    file_id: UUID | None = None
    symbol_id: UUID | None = None
    description: str | None = None
    parent_node_id: UUID | None = None


class ArchitectureEdge(BaseModel):
    """A directed relationship between two architecture nodes."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    relation_type: ArchitectureRelationType

    @model_validator(mode="after")
    def reject_self_reference(self) -> "ArchitectureEdge":
        if self.source_node_id == self.target_node_id:
            raise ValueError("architecture edges cannot reference the same node")
        return self


class ArchitectureMap(BaseModel):
    """The complete graph consumed by the architecture-map frontend."""

    project_id: UUID
    nodes: list[ArchitectureNode] = Field(default_factory=list)
    edges: list[ArchitectureEdge] = Field(default_factory=list)
