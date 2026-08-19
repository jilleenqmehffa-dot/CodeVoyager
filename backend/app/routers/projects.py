from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.core.exceptions import ProjectNotFoundError
from app.repositories.projects import ProjectRepository, get_project_repository
from app.schemas.projects import LocalProjectImportRequest, ProjectSchema
from app.services.projects import import_local_project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/import/local",
    response_model=ProjectSchema,
    status_code=status.HTTP_201_CREATED,
)
async def import_local_project_route(
    payload: LocalProjectImportRequest,
    repository: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> ProjectSchema:
    project = import_local_project(payload.name, payload.local_path, repository)
    return ProjectSchema.model_validate(project.model_dump())


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_route(
    project_id: UUID,
    repository: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> Response:
    if not repository.delete(project_id):
        raise ProjectNotFoundError(f"Project not found: {project_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
