class CodeVoyagerError(Exception):
    """Base class for errors that may safely be returned by the API."""

    status_code = 500
    code = "codevoyager_error"

    def __init__(self, message: str = "CodeVoyager internal error") -> None:
        super().__init__(message)
        self.message = message


class ProjectNotFoundError(CodeVoyagerError):
    status_code = 404
    code = "project_not_found"


class InvalidLocalProjectError(CodeVoyagerError):
    """Raised when a local project directory cannot be imported."""

    status_code = 400
    code = "invalid_local_project"


class ProjectAlreadyExistsError(CodeVoyagerError):
    """Raised when the same local directory has already been imported."""

    status_code = 409
    code = "project_already_exists"


class ProjectAnalysisError(CodeVoyagerError):
    pass


class ArchitectureNotFoundError(CodeVoyagerError):
    status_code = 404
    code = "architecture_not_found"
