from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.models.projects import Project
from app.schemas.projects import ProjectSchema


@pytest.mark.parametrize("project_type", [Project, ProjectSchema])
def test_project_contains_only_required_data(project_type: type[Project]) -> None:
    project = project_type(name=" CodeVoyager ", local_path="/tmp/codevoyager")

    assert isinstance(project.id, UUID)
    assert project.name == "CodeVoyager"
    assert project.local_path == Path("/tmp/codevoyager")
    assert set(project.model_dump()) == {"id", "name", "local_path"}


@pytest.mark.parametrize("project_type", [Project, ProjectSchema])
def test_project_name_cannot_be_empty(project_type: type[Project]) -> None:
    with pytest.raises(ValidationError):
        project_type(name="   ", local_path="/tmp/codevoyager")
