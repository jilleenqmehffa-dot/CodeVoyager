import json
from collections.abc import Sequence

from app.models.project_overview import ProjectOverview
from app.models.projects import Project
from app.repositories.project_overview import ProjectOverviewRepository
from app.repositories.projects import ProjectRepository
from app.services.project_overview_llm import (
    LLMMessage,
    generate_and_send_project_overview,
    send_project_overview_to_llm,
)


class FakeProjectOverviewLLMClient:
    def __init__(self) -> None:
        self.messages: Sequence[LLMMessage] = []

    def complete(self, messages: Sequence[LLMMessage]) -> str:
        self.messages = messages
        return "项目概览分析结果"


def test_send_project_overview_json_to_llm_client() -> None:
    client = FakeProjectOverviewLLMClient()
    overview_json = json.dumps({"languages": ["Python"]})

    response = send_project_overview_to_llm(overview_json, client)

    assert response == "项目概览分析结果"
    assert [message.role for message in client.messages] == ["system", "user"]
    assert client.messages[1].content == overview_json


def test_generate_and_send_project_overview(tmp_path) -> None:
    database_path = tmp_path / "project-overview-llm.db"
    project_repository = ProjectRepository(database_path)
    overview_repository = ProjectOverviewRepository(database_path)
    project = project_repository.create(
        Project(name="CodeVoyager", local_path=tmp_path / "CodeVoyager")
    )
    overview_repository.save(
        ProjectOverview(project_id=project.id, languages=["Python"])
    )
    client = FakeProjectOverviewLLMClient()

    response = generate_and_send_project_overview(
        project.id,
        overview_repository,
        client,
    )

    assert response == "项目概览分析结果"
    assert json.loads(client.messages[1].content)["languages"] == ["Python"]


def test_missing_overview_is_not_sent_to_llm(tmp_path) -> None:
    repository = ProjectOverviewRepository(tmp_path / "missing-overview.db")
    project = Project(name="CodeVoyager", local_path=tmp_path / "CodeVoyager")
    client = FakeProjectOverviewLLMClient()

    response = generate_and_send_project_overview(project.id, repository, client)

    assert response is None
    assert client.messages == []
