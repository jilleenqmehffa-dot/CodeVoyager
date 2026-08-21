from pathlib import Path

from app.models.project_files import ProjectFile
from app.models.projects import Project
from app.repositories.code_imports import CodeImportRepository
from app.repositories.code_symbols import CodeSymbolRepository
from app.repositories.inheritance_relations import InheritanceRelationRepository
from app.repositories.project_files import ProjectFileRepository
from app.repositories.projects import ProjectRepository
from app.services.file_relationship_analyzer import analyze_file_relationships
from app.services.python_static_analyzer import analyze_and_save_project


def test_analyze_file_relationships_builds_python_code_graph(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    package_path = project_path / "app"
    package_path.mkdir(parents=True)
    (package_path / "base.py").write_text(
        "class Base:\n    pass\n\ndef helper():\n    return None\n",
        encoding="utf-8",
    )
    (package_path / "service.py").write_text(
        "from app.base import Base, helper\n\n"
        "class Child(Base):\n"
        "    def run(self, value: Base):\n"
        "        helper()\n"
        "        return value\n",
        encoding="utf-8",
    )

    project = Project(name="example", local_path=project_path)
    database_path = tmp_path / "relationships.db"
    project_repository = ProjectRepository(database_path)
    file_repository = ProjectFileRepository(database_path)
    symbol_repository = CodeSymbolRepository(database_path)
    import_repository = CodeImportRepository(database_path)
    inheritance_repository = InheritanceRelationRepository(database_path)
    project_repository.create(project)
    files = [
        _python_file(project, "app/base.py"),
        _python_file(project, "app/service.py"),
    ]
    file_repository.save_many(project.id, files)
    analyze_and_save_project(
        project,
        file_repository,
        symbol_repository,
        import_repository,
        inheritance_repository,
    )

    relationships = analyze_file_relationships(
        project,
        file_repository,
        symbol_repository,
    )

    assert any(
        item.source_type == "file"
        and item.target_type == "file"
        and item.relationship_type == "import"
        for item in relationships
    )
    assert any(
        item.source_module == "app.service"
        and item.target_module == "app.base"
        for item in relationships
    )
    assert any(
        item.relationship_type == "inheritance" and item.target_name == "Base"
        for item in relationships
    )
    assert any(
        item.relationship_type == "call" and item.target_name == "helper"
        for item in relationships
    )
    assert any(
        item.relationship_type == "reference" and item.target_name == "Base"
        for item in relationships
    )

    for repository in (
        project_repository,
        file_repository,
        symbol_repository,
        import_repository,
        inheritance_repository,
    ):
        repository.engine.dispose()


def _python_file(project: Project, path: str) -> ProjectFile:
    return ProjectFile(
        project_id=project.id,
        path=path,
        name=Path(path).name,
        file_type=".py",
        language="Python",
        category="source",
        is_directory=False,
    )
