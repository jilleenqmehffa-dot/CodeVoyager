from pathlib import Path

import pytest

from app.models.architecture import ArchitectureEdge, ArchitectureMap, ArchitectureNode
from app.models.code_imports import CodeImport
from app.models.code_symbols import CodeSymbol
from app.models.project_files import ProjectFile
from app.models.project_overview import ProjectOverview
from app.models.projects import Project
from app.repositories.architecture import ArchitectureRepository
from app.repositories.projects import ProjectRepository
from app.services.architecture_map_builder import build_architecture_map


def test_builder_creates_categories_modules_and_local_import_edges() -> None:
    project = Project(name="CodeVoyager", local_path="/tmp/codevoyager")
    router_file = ProjectFile(
        project_id=project.id, path="app/routers/projects.py", name="projects.py",
        file_type=".py", language="Python", category="source", is_directory=False,
    )
    service_file = ProjectFile(
        project_id=project.id, path="app/services/projects.py", name="projects.py",
        file_type=".py", language="Python", category="source", is_directory=False,
    )
    symbol = CodeSymbol(
        project_id=project.id, file_id=router_file.id, name="get_project",
        symbol_type="function", start_line=1, end_line=3,
    )
    code_import = CodeImport(
        project_id=project.id, file_id=router_file.id,
        module="app.services.projects", line=1,
    )
    overview = ProjectOverview(
        project_id=project.id, purpose="Explore the codebase",
        databases=["SQLite"], core_modules=["Scanner"], apis=["REST API"],
    )

    result = build_architecture_map(
        project, [router_file, service_file], [symbol], [code_import], overview
    )

    categories = {node.node_type: node for node in result.nodes if node.node_type != "module"}
    assert set(categories) == {"project", "api", "service", "database", "core"}
    router_node = next(node for node in result.nodes if node.file_id == router_file.id)
    service_node = next(node for node in result.nodes if node.file_id == service_file.id)
    assert router_node.parent_node_id == categories["api"].id
    assert router_node.symbol_id == symbol.id
    assert service_node.parent_node_id == categories["service"].id
    assert any(
        edge.source_node_id == router_node.id
        and edge.target_node_id == service_node.id
        and edge.relation_type == "imports"
        for edge in result.edges
    )
    assert {node.name for node in result.nodes} >= {"SQLite", "Scanner", "REST API"}


def test_repository_replaces_and_reads_a_complete_graph(tmp_path: Path) -> None:
    database_path = tmp_path / "architecture.db"
    project = Project(name="Demo", local_path=tmp_path / "demo")
    ProjectRepository(database_path).create(project)
    repository = ArchitectureRepository(database_path)
    root = ArchitectureNode(project_id=project.id, name="Demo", node_type="project")
    api = ArchitectureNode(
        project_id=project.id, name="API", node_type="api", parent_node_id=root.id
    )
    edge = ArchitectureEdge(
        project_id=project.id, source_node_id=root.id,
        target_node_id=api.id, relation_type="contains",
    )
    first = ArchitectureMap(project_id=project.id, nodes=[root, api], edges=[edge])

    repository.save(first)
    assert repository.get_by_project_id(project.id) is not None
    replacement = ArchitectureMap(project_id=project.id, nodes=[root], edges=[])
    repository.save(replacement)

    stored = repository.get_by_project_id(project.id)
    assert stored is not None
    assert [node.id for node in stored.nodes] == [root.id]
    assert stored.edges == []


def test_repository_rejects_edges_to_nodes_outside_map(tmp_path: Path) -> None:
    project = Project(name="Demo", local_path=tmp_path / "demo")
    root = ArchitectureNode(project_id=project.id, name="Demo", node_type="project")
    invalid = ArchitectureEdge(
        project_id=project.id, source_node_id=root.id,
        target_node_id=ArchitectureNode(
            project_id=project.id, name="API", node_type="api"
        ).id,
        relation_type="contains",
    )

    with pytest.raises(ValueError, match="reference nodes"):
        ArchitectureRepository(tmp_path / "architecture.db").save(
            ArchitectureMap(project_id=project.id, nodes=[root], edges=[invalid])
        )
