from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

ProjectFileCategory = Literal[
    "source",
    "test",
    "docs",
    "readme",
    "config",
    "dependency",
    "dockerfile",
    "compose",
    "other",
]


class ProjectFile(BaseModel):
    """A file or directory discovered inside an imported project."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    path: str = Field(min_length=1)
    name: str = Field(min_length=1)
    file_type: str | None = None
    language: str | None = None
    category: ProjectFileCategory
    is_directory: bool
