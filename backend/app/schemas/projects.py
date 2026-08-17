from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class LocalProjectImportRequest(BaseModel):
    """Data required to import an existing local project."""

    model_config = ConfigDict(str_strip_whitespace=True)

    local_path: str = Field(min_length=1, max_length=4096)


class ProjectSchema(BaseModel):
    """Project data exposed through the API."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=255)
    local_path: Path
