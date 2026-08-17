from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.projects import ProjectSourceType


class ProjectSchema(BaseModel):
    """Project import data schema."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=255)
    source_type: ProjectSourceType
    source_url: HttpUrl | None = None
    local_path: Path


class ProjectUrlValidationRequest(BaseModel):
    """Payload used to validate a repository URL before importing it."""

    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(min_length=1, max_length=2048)


class ProjectUrlValidationResponse(BaseModel):
    valid: bool = True
    url: str
