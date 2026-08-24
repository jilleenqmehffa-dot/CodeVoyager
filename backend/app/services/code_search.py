from uuid import UUID

from app.core.exceptions import FileReadError
from app.models.projects import Project
from app.repositories.code_symbols import CodeSymbolRepository
from app.repositories.project_files import ProjectFileRepository
from app.schemas.code_search import SymbolSearchResultSchema, TextSearchResultSchema
from app.services.read_file import read_file


def search_text(
    project: Project,
    query: str,
    file_repository: ProjectFileRepository,
) -> list[TextSearchResultSchema]:
    """Search scanned text files without rediscovering the project tree."""

    results: list[TextSearchResultSchema] = []
    for project_file in file_repository.get_by_project_id(project.id):
        if project_file.is_directory or project_file.language is None:
            continue
        try:
            content = read_file(project.local_path, project_file)
        except FileReadError:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if query in line:
                results.append(
                    TextSearchResultSchema(
                        file_id=project_file.id,
                        file_path=project_file.path,
                        line_number=line_number,
                        matched_text=line,
                    )
                )
    return results


def find_symbol(
    project_id: UUID,
    symbol_name: str,
    symbol_repository: CodeSymbolRepository,
    file_repository: ProjectFileRepository,
) -> list[SymbolSearchResultSchema]:
    """Find previously analyzed class, function, and method definitions."""

    files = {
        project_file.id: project_file
        for project_file in file_repository.get_by_project_id(project_id)
    }
    results: list[SymbolSearchResultSchema] = []
    for symbol in symbol_repository.find_by_name(project_id, symbol_name):
        project_file = files.get(symbol.file_id)
        if project_file is None:
            continue
        results.append(
            SymbolSearchResultSchema(
                symbol_id=symbol.id,
                symbol_name=symbol.name,
                symbol_type=symbol.symbol_type,
                file_id=symbol.file_id,
                file_path=project_file.path,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
            )
        )
    return results
