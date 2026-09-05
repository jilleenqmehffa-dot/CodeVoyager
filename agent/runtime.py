"""Agent 创建与运行入口。"""

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel


def run_agent(message: str, model: str | BaseChatModel) -> dict:
    """使用传入的模型创建 Agent 并运行，返回消息状态。"""
    agent = create_agent(model=model, tools=[])
    return agent.invoke({"messages": [{"role": "user", "content": message}]})
