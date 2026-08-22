from dataclasses import dataclass
from typing import Protocol, Sequence
from uuid import UUID

from app.repositories.project_overview import ProjectOverviewRepository
from app.services.project_overview_generator import generate_project_overview_json

PROJECT_OVERVIEW_SYSTEM_PROMPT = (
    "你是一个软件项目分析助手。请根据提供的项目概览 JSON，"
    "总结项目架构、关键技术和运行测试方式。不要编造 JSON 中不存在的信息。"
)


@dataclass(frozen=True)
class LLMMessage:
    """A provider-neutral chat message sent to a large language model."""

    role: str
    content: str


class ProjectOverviewLLMClient(Protocol):
    """Interface to implement when a concrete LLM provider is introduced."""

    def complete(self, messages: Sequence[LLMMessage]) -> str:
        """Send chat messages to the model and return its text response."""

        ...


def send_project_overview_to_llm(
    project_overview_json: str,
    client: ProjectOverviewLLMClient,
) -> str:
    """Send serialized project overview data through an injected LLM client."""

    messages = [
        LLMMessage(role="system", content=PROJECT_OVERVIEW_SYSTEM_PROMPT),
        LLMMessage(role="user", content=project_overview_json),
    ]
    return client.complete(messages)


def generate_and_send_project_overview(
    project_id: UUID,
    repository: ProjectOverviewRepository,
    client: ProjectOverviewLLMClient,
) -> str | None:
    """Query a project overview, serialize it, and send it to an LLM."""

    project_overview_json = generate_project_overview_json(project_id, repository)
    if project_overview_json is None:
        return None
    return send_project_overview_to_llm(project_overview_json, client)
