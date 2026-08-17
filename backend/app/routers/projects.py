from fastapi import APIRouter, status

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
) -> ProjectSchema:
    project = import_local_project(payload.local_path)
    return ProjectSchema.model_validate(project.model_dump())
