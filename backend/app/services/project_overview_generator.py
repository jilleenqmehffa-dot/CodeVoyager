from uuid import UUID

from app.repositories.project_overview import ProjectOverviewRepository


def generate_project_overview_json(
    project_id: UUID,
    repository: ProjectOverviewRepository,
) -> str | None:
    """Query and serialize a project's overview as JSON."""

    overview = repository.get_by_project_id(project_id)
    if overview is None:
        return None

    project_overview_json = overview.model_dump_json()
    return project_overview_json
