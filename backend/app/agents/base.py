"""Agent 基类 — 所有专用 Agent 的通用接口和共享逻辑。"""

from typing import AsyncIterator

from app.domain import RetrievedChunk
from app.llm.providers.base import ChatProvider


class AgentContext:
    """传递给 Agent 的上下文信息。"""

    def __init__(
        self,
        question: str,
        history_context: str = '',
        retrieved_chunks: list[RetrievedChunk] | None = None,
        temperature: float = 0.7,
        model: str = '',
    ) -> None:
        self.question = question
        self.history_context = history_context
        self.retrieved_chunks = retrieved_chunks or []
        self.temperature = temperature
        self.model = model


class BaseAgent:
    """所有 Agent 的基类。"""

    name: str = ''
    label: str = ''
    description: str = ''
    system_prompt: str = ''

    def __init__(self, provider: ChatProvider) -> None:
        self.provider = provider

    async def execute(self, ctx: AgentContext) -> str:
        """执行 Agent 任务，返回结果文本。"""
        user_message = self._build_user_message(ctx)
        try:
            result = await self.provider.complete(
                system_prompt=self.system_prompt,
                user_message=user_message,
                temperature=ctx.temperature,
                model=ctx.model,
            )
            return result.strip() if result else f'[{self.label}] 未生成输出'
        except Exception as exc:
            return f'[{self.label}] 执行出错：{exc}'

    def _build_user_message(self, ctx: AgentContext) -> str:
        """子类可重写此方法以自定义发送给 LLM 的消息内容。"""
        parts = [f'## 用户提问\n{ctx.question}']

        if ctx.history_context:
            parts.append(f'## 对话上下文\n{ctx.history_context}')

        if ctx.retrieved_chunks:
            docs_text = '\n\n'.join(
                f'[来自 {chunk.filename}]\n{chunk.content[:500]}'
                for chunk in ctx.retrieved_chunks
            )
            parts.append(f'## 检索到的文档片段\n{docs_text}')

        parts.append(f'## 你的任务\n{self.description}')
        return '\n\n---\n\n'.join(parts)
