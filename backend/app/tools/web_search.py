"""
联网搜索工具 — 让 AI 能搜索互联网获取实时信息。
支持多个搜索后端（DuckDuckGo / Bing），搜索失败时返回友好提示。
注意：初始化时使用短超时快速失败，不阻塞主流程。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SearchResult:
    def __init__(self, title: str, url: str, snippet: str) -> None:
        self.title = title
        self.url = url
        self.snippet = snippet


class BaseSearchBackend(ABC):
    """搜索后端抽象基类"""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        ...

    @abstractmethod
    def available(self) -> bool:
        ...


# ── DuckDuckGo 后端 ──────────────────────────────────────────────

class DuckDuckGoBackend(BaseSearchBackend):
    """DuckDuckGo 搜索后端（国际服务器用，国内不可用）"""

    def __init__(self) -> None:
        self._client: Any | None = None
        self._ok: bool | None = None

    def available(self) -> bool:
        if self._ok is False:
            return False
        if self._client is not None:
            return True
        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS(timeout=2)
            test = list(ddgs.text('test', max_results=1))
            if test:
                self._client = ddgs
                self._ok = True
                return True
        except Exception as exc:
            logger.warning('DuckDuckGo: unavailable (%s)', exc)
        self._ok = False
        return False

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.available():
            return []
        try:
            raw = list(self._client.text(query, max_results=max_results))
            return [
                SearchResult(
                    title=r.get('title', ''),
                    url=r.get('href', ''),
                    snippet=r.get('body', ''),
                )
                for r in raw if r.get('body')
            ]
        except Exception as exc:
            logger.warning('DuckDuckGo: search failed (%s)', exc)
            return []


# ── Bing 搜索后端 ────────────────────────────────────────────────

class BingBackend(BaseSearchBackend):
    """Bing Web Search API 后端（国内可用，需 API Key）"""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._ok: bool | None = None

    def available(self) -> bool:
        if self._ok is False:
            return False
        if not self._api_key:
            self._ok = False
            return False
        # 轻量检查：API Key 非空即认为可用（实际调用时失败再降级）
        self._ok = True
        return True

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.available():
            return []
        try:
            resp = httpx.get(
                'https://api.bing.microsoft.com/v7.0/search',
                params={'q': query, 'count': max_results, 'mkt': 'zh-CN'},
                headers={'Ocp-Apim-Subscription-Key': self._api_key},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get('webPages', {}).get('value', []):
                snippet = item.get('snippet', '')
                if snippet:
                    results.append(SearchResult(
                        title=item.get('name', ''),
                        url=item.get('url', ''),
                        snippet=snippet,
                    ))
            return results
        except Exception as exc:
            logger.warning('Bing: search failed (%s)', exc)
            self._ok = False  # 失败后标记为不可用，避免重复重试
            return []


# ── 工厂函数 ─────────────────────────────────────────────────────

def create_search_backend(backend_name: str, api_key: str = '') -> BaseSearchBackend:
    """根据配置创建搜索后端实例"""
    backend_name = backend_name.lower()
    if backend_name == 'bing':
        return BingBackend(api_key)
    # 默认 DuckDuckGo
    return DuckDuckGoBackend()


class WebSearchTool:
    """联网搜索工具 — 延迟初始化，不阻塞主流程。"""

    def __init__(self, backend_name: str = 'duckduckgo', api_key: str = '') -> None:
        self._backend = create_search_backend(backend_name, api_key)
        self._backend_name = backend_name

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return self._backend.search(query, max_results)

    def search_formatted(self, query: str, max_results: int = 5) -> str:
        results = self.search(query, max_results)
        if not self._backend.available():
            return '〈搜索服务暂不可用，请检查网络连接或 API Key 配置〉'
        if not results:
            return '〈未找到相关搜索结果〉'
        lines = ['以下是联网搜索结果：\n']
        for i, r in enumerate(results, 1):
            lines.append(f'{i}. {r.title}')
            lines.append(f'   {r.snippet}')
            lines.append(f'   来源: {r.url}\n')
        return '\n'.join(lines)
