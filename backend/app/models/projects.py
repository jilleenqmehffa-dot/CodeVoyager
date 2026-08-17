from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProjectSourceType(StrEnum):

    GITHUB = "github"
    LOCAL = "local"


class Project(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=255)
    source_type: ProjectSourceType
    source_url: HttpUrl | None = None
    local_path: Path
