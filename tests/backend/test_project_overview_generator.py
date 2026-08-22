import json

from app.models.project_overview import ProjectOverview
from app.models.projects import Project
from app.repositories.project_overview import ProjectOverviewRepository
from app.repositories.projects import ProjectRepository
from app.services.project_overview_generator import generate_project_overview_json


def test_query_and_serialize_project_overview(tmp_path) -> None:
    database_path = tmp_path / "project-overview.db"
    project_repository = ProjectRepository(database_path)
    overview_repository = ProjectOverviewRepository(database_path)
    project = project_repository.create(
        Project(name="CodeVoyager", local_path=tmp_path / "CodeVoyager")
    )
    overview = ProjectOverview(
        project_id=project.id,
        purpose="Explore an unfamiliar codebase",
        project_type="web application",
        tech_stack=["FastAPI", "React"],
        languages=["Python", "TypeScript"],
        dependencies=["fastapi", "react"],
        core_modules=["scanner", "static analysis"],
        entrypoints=["backend/app/main.py"],
        configuration_systems=["environment variables"],
        databases=["SQLite"],
        apis=["REST API"],
        test_methods=["pytest"],
        run_commands=["./scripts/dev.sh"],
    )
    overview_repository.save(overview)

    overview_json = generate_project_overview_json(
        project.id,
        overview_repository,
    )

    assert overview_json is not None
    assert json.loads(overview_json) == overview.model_dump(mode="json")


def test_generate_project_overview_json_returns_none_when_missing(tmp_path) -> None:
    database_path = tmp_path / "missing-overview.db"
    project_repository = ProjectRepository(database_path)
    overview_repository = ProjectOverviewRepository(database_path)
    project = project_repository.create(
        Project(name="CodeVoyager", local_path=tmp_path / "CodeVoyager")
    )

    assert generate_project_overview_json(project.id, overview_repository) is None
