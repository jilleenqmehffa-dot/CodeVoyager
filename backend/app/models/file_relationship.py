from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

RelationshipEntityType = Literal["file", "module", "class", "function"]
RelationshipType = Literal["import", "call", "inheritance", "reference"]


class FileRelationship(BaseModel):
    """A directed relationship between two entities in a project's code graph."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    relationship_type: RelationshipType

    source_type: RelationshipEntityType
    target_type: RelationshipEntityType
    source_file_id: UUID
    target_file_id: UUID | None = None
    source_symbol_id: UUID | None = None
    target_symbol_id: UUID | None = None
    source_module: str | None = Field(default=None, min_length=1)
    target_module: str | None = Field(default=None, min_length=1)
    target_name: str | None = Field(default=None, min_length=1)

    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_entity_locations(self) -> "FileRelationship":
        """Require enough information to locate both ends of the relationship."""

        if self.source_type == "module" and self.source_module is None:
            raise ValueError("source_module is required for a module source")
        if self.source_type in {"class", "function"} and self.source_symbol_id is None:
            raise ValueError("source_symbol_id is required for a symbol source")

        if self.target_type == "file" and self.target_file_id is None:
            raise ValueError("target_file_id is required for a file target")
        if (
            self.target_type == "module"
            and self.target_module is None
            and self.target_file_id is None
        ):
            raise ValueError(
                "target_module or target_file_id is required for a module target"
            )
        if (
            self.target_type in {"class", "function"}
            and self.target_symbol_id is None
            and self.target_name is None
        ):
            raise ValueError(
                "target_symbol_id or target_name is required for a symbol target"
            )
        return self
