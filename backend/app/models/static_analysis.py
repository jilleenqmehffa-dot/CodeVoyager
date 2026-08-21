from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.code_imports import CodeImport
from app.models.code_symbols import CodeSymbol
from app.models.inheritance_relations import InheritanceRelation


class PythonAnalysisFailure(BaseModel):
    """A Python source file that could not be read or parsed."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file_id: UUID
    path: str = Field(min_length=1)
    error: str = Field(min_length=1)


class PythonStaticAnalysisResult(BaseModel):
    """Structured output from analyzing a project's Python source files."""

    symbols: list[CodeSymbol] = Field(default_factory=list)
    imports: list[CodeImport] = Field(default_factory=list)
    inheritance_relations: list[InheritanceRelation] = Field(default_factory=list)
    failures: list[PythonAnalysisFailure] = Field(default_factory=list)
