from uuid import uuid4

from app.models import ProjectOverview


def test_project_overview_contains_all_summary_sections() -> None:
    project_id = uuid4()
    overview = ProjectOverview(
        project_id=project_id,
        purpose=" Explore an unfamiliar codebase ",
        project_type="web application",
        tech_stack=["FastAPI", "React"],
        languages=["Python", "TypeScript"],
        dependencies=["fastapi", "react"],
        core_modules=["scanner", "static analysis"],
        entrypoints=["backend/app/main.py", "frontend/src/main.tsx"],
        configuration_systems=["environment variables"],
        databases=["SQLite"],
        apis=["REST API"],
        test_methods=["pytest"],
        run_commands=["./scripts/dev.sh"],
    )

    assert overview.project_id == project_id
    assert overview.purpose == "Explore an unfamiliar codebase"
    assert overview.tech_stack == ["FastAPI", "React"]
    assert overview.run_commands == ["./scripts/dev.sh"]


def test_project_overview_collection_fields_default_to_independent_lists() -> None:
    first = ProjectOverview(project_id=uuid4())
    second = ProjectOverview(project_id=uuid4())

    first.languages.append("Python")

    assert second.languages == []
    assert first.model_dump().keys() == {
        "id",
        "project_id",
        "purpose",
        "project_type",
        "tech_stack",
        "languages",
        "dependencies",
        "core_modules",
        "entrypoints",
        "configuration_systems",
        "databases",
        "apis",
        "test_methods",
        "run_commands",
    }
