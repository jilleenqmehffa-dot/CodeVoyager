from uuid import UUID

from pydantic import BaseModel


class ProjectFileContentSchema(BaseModel):
    """File metadata and source text returned to the code viewer."""

    id: UUID
    project_id: UUID
    path: str
    name: str
    file_type: str | None
    language: str | None
    content: str
