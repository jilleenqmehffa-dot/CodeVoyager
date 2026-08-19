from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class InheritanceRelation(BaseModel):
    """A class inheritance declaration, optionally linked to a local class."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    child_symbol_id: UUID
    parent_name: str = Field(min_length=1)
    parent_symbol_id: UUID | None = None
