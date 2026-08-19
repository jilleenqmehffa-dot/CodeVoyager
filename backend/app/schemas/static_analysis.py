from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.code_imports import CodeImport
from app.models.code_symbols import CodeSymbol
from app.models.inheritance_relations import InheritanceRelation


class CodeSymbolSchema(CodeSymbol):
    """Code symbol data exposed outside the analysis domain layer."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class CodeImportSchema(CodeImport):
    """Python import data exposed outside the analysis domain layer."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class InheritanceRelationSchema(InheritanceRelation):
    """Class inheritance data exposed outside the analysis domain layer."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class PythonAnalysisFailureSchema(BaseModel):
    """A source file that could not be read or parsed."""

    model_config = ConfigDict(str_strip_whitespace=True)

    file_id: UUID
    path: str = Field(min_length=1)
    error: str = Field(min_length=1)


class PythonStaticAnalysisResultSchema(BaseModel):
    """Structured output from analyzing a project's Python source files."""

    symbols: list[CodeSymbolSchema] = Field(default_factory=list)
    imports: list[CodeImportSchema] = Field(default_factory=list)
    inheritance_relations: list[InheritanceRelationSchema] = Field(
        default_factory=list
    )
    failures: list[PythonAnalysisFailureSchema] = Field(default_factory=list)


# Preserve the existing service-facing names while exposing explicit API schemas.
PythonAnalysisFailure = PythonAnalysisFailureSchema
PythonStaticAnalysisResult = PythonStaticAnalysisResultSchema
