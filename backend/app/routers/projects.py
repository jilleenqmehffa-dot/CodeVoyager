from fastapi import APIRouter

from app.schemas.projects import (
    ProjectUrlValidationRequest,
    ProjectUrlValidationResponse,
)
from app.services.projects import validate_github_url

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/validate-url", response_model=ProjectUrlValidationResponse)
async def validate_project_url(
    payload: ProjectUrlValidationRequest,
) -> ProjectUrlValidationResponse:
    normalized_url = validate_github_url(payload.url)
    return ProjectUrlValidationResponse(url=normalized_url)
