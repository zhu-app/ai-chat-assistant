"""
联网搜索工具 — 让 AI 能搜索互联网获取实时信息。
支持多个搜索后端（DuckDuckGo / Bing / 百度千帆），搜索失败时返回友好提示。
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
            self._ok = False
            return []


# ── 百度千帆搜索后端 ─────────────────────────────────────────────

class QianfanBackend(BaseSearchBackend):
    """百度千帆搜索后端（国内可用，需千帆平台 API Key + Secret Key）

    在千帆平台「工具中心」添加「百度搜索」工具后，获取工具 ID (pluginId) 和 API 凭证。
    工具中心地址: https://console.bce.baidu.com/qianfan/tools/toolsCenter/
    """

    TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
    PLUGIN_API = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin/'

    def __init__(self, api_key: str, secret_key: str, plugin_id: str = '') -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._plugin_id = plugin_id
        self._access_token: str | None = None
        self._ok: bool | None = None

    def _get_access_token(self) -> str | None:
        """获取千帆平台 access_token（有效期 30 天，内部缓存）"""
        if self._access_token:
            return self._access_token
        try:
            resp = httpx.post(
                self.TOKEN_URL,
                params={
                    'grant_type': 'client_credentials',
                    'client_id': self._api_key,
                    'client_secret': self._secret_key,
                },
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            token = data.get('access_token')
            if token:
                self._access_token = token
                return token
            logger.warning('Qianfan: no access_token in response: %s', data)
        except Exception as exc:
            logger.warning('Qianfan: get token failed (%s)', exc)
        return None

    def available(self) -> bool:
        if self._ok is False:
            return False
        if not self._api_key or not self._secret_key:
            logger.warning('Qianfan: missing api_key or secret_key')
            self._ok = False
            return False
        token = self._get_access_token()
        if token:
            self._ok = True
            return True
        self._ok = False
        return False

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.available():
            return []
        token = self._get_access_token()
        if not token:
            self._ok = False
            return []

        try:
            pid = self._plugin_id or 'baidu-search'
            resp = httpx.post(
                f'{self.PLUGIN_API}{pid}/',
                params={'access_token': token},
                json={'query': query, 'stream': False},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            # 千帆插件返回格式可能为 { "result": [...] } 或 { "results": [...] }
            raw_results = data.get('result') or data.get('results') or data.get('data') or []
            if isinstance(raw_results, dict):
                # 有时结果在嵌套字段中
                raw_results = raw_results.get('items') or raw_results.get('list') or []

            results = []
            for item in (raw_results or []):
                if isinstance(item, dict):
                    title = item.get('title') or item.get('name') or ''
                    url = item.get('url') or item.get('link') or item.get('href') or ''
                    snippet = item.get('snippet') or item.get('abstract') or item.get('desc') or ''
                    if snippet:
                        results.append(SearchResult(title=title, url=url, snippet=snippet))
            return results

        except Exception as exc:
            logger.warning('Qianfan: search failed (%s)', exc)
            self._ok = False
            return []


# ── 工厂函数 ─────────────────────────────────────────────────────

def create_search_backend(
    backend_name: str,
    api_key: str = '',
    secret_key: str = '',
    plugin_id: str = '',
) -> BaseSearchBackend:
    """根据配置创建搜索后端实例"""
    backend_name = backend_name.lower()

    if backend_name == 'bing':
        return BingBackend(api_key)

    if backend_name == 'qianfan':
        return QianfanBackend(api_key, secret_key, plugin_id)

    # 默认 DuckDuckGo
    return DuckDuckGoBackend()


class WebSearchTool:
    """联网搜索工具 — 延迟初始化，不阻塞主流程。"""

    def __init__(
        self,
        backend_name: str = 'duckduckgo',
        api_key: str = '',
        secret_key: str = '',
        plugin_id: str = '',
    ) -> None:
        self._backend = create_search_backend(backend_name, api_key, secret_key, plugin_id)

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
