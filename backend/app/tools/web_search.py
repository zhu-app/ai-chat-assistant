"""
联网搜索工具 — 让 AI 能搜索互联网获取实时信息。
支持多个搜索后端，搜索失败时返回友好提示。
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SearchResult:
    def __init__(self, title: str, url: str, snippet: str) -> None:
        self.title = title
        self.url = url
        self.snippet = snippet


class WebSearchTool:
    """联网搜索工具 — 自动选择可用的搜索后端。"""

    def __init__(self) -> None:
        self._backend = self._init_backend()

    @staticmethod
    def _init_backend() -> Any:
        # 优先 DuckDuckGo（免费，无需 API Key）
        try:
            from duckduckgo_search import DDGS
            test = list(DDGS().text('test', max_results=1))
            if test:
                return DDGS()
        except Exception as exc:
            logger.warning('WebSearch: DuckDuckGo unavailable (%s)', exc)
        return None

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._backend:
            return []
        try:
            raw = list(self._backend.text(query, max_results=max_results))
            return [
                SearchResult(
                    title=r.get('title', ''),
                    url=r.get('href', ''),
                    snippet=r.get('body', ''),
                )
                for r in raw if r.get('body')
            ]
        except Exception as exc:
            logger.warning('WebSearch: search failed (%s)', exc)
            return []

    def search_formatted(self, query: str, max_results: int = 5) -> str:
        results = self.search(query, max_results)
        if not self._backend:
            return '〈搜索服务暂不可用，请检查网络连接〉'
        if not results:
            return '〈未找到相关搜索结果〉'
        lines = ['以下是联网搜索结果：\n']
        for i, r in enumerate(results, 1):
            lines.append(f'{i}. {r.title}')
            lines.append(f'   {r.snippet}')
            lines.append(f'   来源: {r.url}\n')
        return '\n'.join(lines)
