from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class CodeImport(BaseModel):
    """One imported name or module found in a Python source file."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    file_id: UUID
    module: str = Field(min_length=1)
    imported_name: str | None = None
    alias: str | None = None
    line: int = Field(ge=1)
