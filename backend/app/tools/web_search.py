"""
联网搜索工具 — 让 AI 能搜索互联网获取实时信息。
支持多个搜索后端，搜索失败时返回友好提示。
注意：初始化时使用短超时快速失败，不阻塞主流程。
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 全局缓存：后端是否可用，避免每次请求都重试超时
_backend_available: bool | None = None


class SearchResult:
    def __init__(self, title: str, url: str, snippet: str) -> None:
        self.title = title
        self.url = url
        self.snippet = snippet


class WebSearchTool:
    """联网搜索工具 — 延迟初始化，不阻塞主流程。"""

    def __init__(self) -> None:
        self._backend: Any | None = None  # 首次搜索时才初始化

    def _ensure_backend(self) -> bool:
        """确保后端已初始化，快速失败（超时 2 秒）。"""
        global _backend_available
        if _backend_available is False:
            return False
        if self._backend is not None:
            return True
        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS(timeout=2)
            test = list(ddgs.text('test', max_results=1))
            if test:
                self._backend = ddgs
                _backend_available = True
                return True
        except Exception as exc:
            logger.warning('WebSearch: DuckDuckGo unavailable (%s)', exc)
        _backend_available = False
        return False

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._ensure_backend():
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
