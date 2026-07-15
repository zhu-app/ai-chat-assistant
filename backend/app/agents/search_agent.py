"""知识库检索 Agent — 从已上传文档中搜索与问题相关的内容。"""

from app.agents.base import BaseAgent, AgentContext
from app.llm.providers.base import ChatProvider

SEARCH_SYSTEM_PROMPT = """你是一个知识库检索分析助手。你的职责是：

1. 阅读下方提供的文档片段
2. 从中提取与用户问题最相关的信息
3. 以简洁、清晰的方式组织这些信息
4. 如果不相关信息不足，如实说明

注意：直接基于文档内容回答，不要编造信息。
"""


class SearchAgent(BaseAgent):
    name = 'search'
    label = '📚 知识检索'
    description = '从知识库文档中检索与问题相关的信息并归纳整理'
    system_prompt = SEARCH_SYSTEM_PROMPT

    def __init__(self, provider: ChatProvider) -> None:
        super().__init__(provider)

    def _build_user_message(self, ctx: AgentContext) -> str:
        parts = [f'## 用户提问\n{ctx.question}']

        if ctx.retrieved_chunks:
            docs_text = '\n\n'.join(
                f'[文件: {chunk.filename} | 相关度: {chunk.score:.0f}]\n{chunk.content}'
                for chunk in ctx.retrieved_chunks
            )
            parts.append(f'## 检索到的文档片段\n{docs_text}')
        else:
            parts.append('## 检索到的文档片段\n（无相关文档）')

        parts.append('## 任务\n从上述文档中提取与问题相关的信息并归纳整理。')
        return '\n\n---\n\n'.join(parts)
