from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.projects import ProjectSourceType


class ProjectSchema(BaseModel):
    """Project import data schema."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=255)
    source_type: ProjectSourceType
    local_path: Path
