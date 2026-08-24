from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.core.exceptions import (
    ArchitectureNotFoundError,
    ProjectFileNotFoundError,
    ProjectNotFoundError,
)
from app.models.architecture import ArchitectureMap
from app.repositories.architecture import (
    ArchitectureRepository,
    get_architecture_repository,
)
from app.repositories.code_imports import CodeImportRepository, get_code_import_repository
from app.repositories.code_symbols import CodeSymbolRepository, get_code_symbol_repository
from app.repositories.project_files import ProjectFileRepository, get_project_file_repository
from app.repositories.project_overview import (
    ProjectOverviewRepository,
    get_project_overview_repository,
)
from app.repositories.projects import ProjectRepository, get_project_repository
from app.schemas.files import ProjectFileContentSchema
from app.schemas.projects import LocalProjectImportRequest, ProjectSchema
from app.services.architecture_map_builder import rebuild_project_architecture
from app.services.projects import import_local_project
from app.services.read_file import read_file

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


@router.get("/{project_id}/architecture", response_model=ArchitectureMap)
async def get_project_architecture_route(
    project_id: UUID,
    project_repository: Annotated[ProjectRepository, Depends(get_project_repository)],
    architecture_repository: Annotated[
        ArchitectureRepository, Depends(get_architecture_repository)
    ],
) -> ArchitectureMap:
    if project_repository.get(project_id) is None:
        raise ProjectNotFoundError(f"Project not found: {project_id}")
    architecture = architecture_repository.get_by_project_id(project_id)
    if architecture is None:
        raise ArchitectureNotFoundError(
            f"Architecture map has not been built: {project_id}"
        )
    return architecture


@router.post(
    "/{project_id}/architecture/rebuild",
    response_model=ArchitectureMap,
    status_code=status.HTTP_201_CREATED,
)
async def rebuild_project_architecture_route(
    project_id: UUID,
    project_repository: Annotated[ProjectRepository, Depends(get_project_repository)],
    architecture_repository: Annotated[
        ArchitectureRepository, Depends(get_architecture_repository)
    ],
    file_repository: Annotated[ProjectFileRepository, Depends(get_project_file_repository)],
    symbol_repository: Annotated[CodeSymbolRepository, Depends(get_code_symbol_repository)],
    import_repository: Annotated[CodeImportRepository, Depends(get_code_import_repository)],
    overview_repository: Annotated[
        ProjectOverviewRepository, Depends(get_project_overview_repository)
    ],
) -> ArchitectureMap:
    project = project_repository.get(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project not found: {project_id}")
    return rebuild_project_architecture(
        project,
        architecture_repository,
        file_repository,
        symbol_repository,
        import_repository,
        overview_repository,
    )


@router.get(
    "/{project_id}/files/{file_id}",
    response_model=ProjectFileContentSchema,
)
async def get_project_file_content_route(
    project_id: UUID,
    file_id: UUID,
    project_repository: Annotated[ProjectRepository, Depends(get_project_repository)],
    file_repository: Annotated[ProjectFileRepository, Depends(get_project_file_repository)],
) -> ProjectFileContentSchema:
    project = project_repository.get(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project not found: {project_id}")
    project_file = file_repository.get(project_id, file_id)
    if project_file is None:
        raise ProjectFileNotFoundError(
            f"Project file not found: {file_id}"
        )
    return ProjectFileContentSchema(
        id=project_file.id,
        project_id=project_file.project_id,
        path=project_file.path,
        name=project_file.name,
        file_type=project_file.file_type,
        language=project_file.language,
        content=read_file(project.local_path, project_file),
    )
