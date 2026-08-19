from pydantic import BaseModel

from app.models.project_files import ProjectFile
from app.models.project_scans import ProjectScan


class ProjectScanResult(BaseModel):
    """Complete structured output from scanning one project."""

    scan: ProjectScan
    files: list[ProjectFile]
