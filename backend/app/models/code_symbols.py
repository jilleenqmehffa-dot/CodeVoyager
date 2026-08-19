from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

CodeSymbolType = Literal["class", "function", "method"]


class CodeSymbol(BaseModel):
    """A class, function, or method found in a Python source file."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    file_id: UUID
    name: str = Field(min_length=1)
    symbol_type: CodeSymbolType
    parent_symbol_id: UUID | None = None
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    parameters: list[str] = Field(default_factory=list)
    docstring: str | None = None
