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


class ProjectAnalysisError(CodeVoyagerError):
    pass
