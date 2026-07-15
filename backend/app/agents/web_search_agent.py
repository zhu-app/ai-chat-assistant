"""
联网搜索 Agent — 当用户问题需要实时信息时，搜索网络并整理结果。
"""

from app.agents.base import BaseAgent, AgentContext
from app.llm.providers.base import ChatProvider
from app.tools.web_search import WebSearchTool

SEARCH_SYSTEM_PROMPT = """你是一个网络搜索专家。你的任务是：
1. 分析用户问题，提取关键搜索词
2. 阅读搜索结果
3. 整理成清晰、有条理的回答
4. 注明信息来源（引用来源 URL）

如果搜索结果不足以回答问题，如实告知用户。"""


class WebSearchAgent(BaseAgent):
    name = 'web_search'
    label = '🌐 联网搜索'
    description = '搜索互联网获取最新信息'

    def __init__(
        self,
        provider: ChatProvider,
        backend_name: str = 'duckduckgo',
        api_key: str = '',
        secret_key: str = '',
        plugin_id: str = '',
    ) -> None:
        super().__init__(provider)
        self.search_tool = WebSearchTool(
            backend_name=backend_name,
            api_key=api_key,
            secret_key=secret_key,
            plugin_id=plugin_id,
        )

    def _build_user_message(self, ctx: AgentContext) -> str:
        # 搜索网络
        search_results = self.search_tool.search_formatted(ctx.question)
        return (
            f'## 用户问题\n{ctx.question}\n\n'
            f'## 搜索结果\n{search_results}\n\n'
            f'## 任务\n基于以上搜索结果回答用户问题，引用来源。'
        )

    async def execute(self, ctx: AgentContext) -> str:
        try:
            result = await self.provider.complete(
                system_prompt=SEARCH_SYSTEM_PROMPT,
                user_message=self._build_user_message(ctx),
                temperature=ctx.temperature,
                model=ctx.model,
            )
            return result.strip() if result else '（搜索未返回结果）'
        except Exception as exc:
            return f'（联网搜索出错：{exc}）'
