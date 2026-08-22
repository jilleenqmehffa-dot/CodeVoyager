from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProjectOverview(BaseModel):
    """A project-level summary produced from repository analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    purpose: str | None = None
    project_type: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    core_modules: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    configuration_systems: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    apis: list[str] = Field(default_factory=list)
    test_methods: list[str] = Field(default_factory=list)
    run_commands: list[str] = Field(default_factory=list)
