"""
联网搜索工具 — 让 AI 能搜索互联网获取实时信息。
支持多个搜索后端（DuckDuckGo / Bing / 百度千帆），搜索失败时返回友好提示。
注意：初始化时使用短超时快速失败，不阻塞主流程。
"""

import json
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
    """百度千帆搜索后端（国内可用，支持 BCE IAM v1 签名认证）

    支持两种密钥格式:
    1. 完整 IAM 密钥: api_key='bce-v3/ALTAK-{ak}/{sk}', secret_key=''
    2. 拆分密钥:     api_key='{ak}', secret_key='{sk}'

    在千帆平台「工具中心」添加「百度搜索」工具后，获取工具 ID (pluginId)。
    工具中心地址: https://console.bce.baidu.com/qianfan/tools/toolsCenter/
    """

    PLUGIN_API = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin/'

    def __init__(self, api_key: str, secret_key: str, plugin_id: str = '') -> None:
        # 解析 BCE IAM 密钥格式: bce-v3/ALTAK-{ak}/{sk}
        if api_key.startswith('bce-v3/ALTAK-') and '/' in api_key:
            parts = api_key.replace('bce-v3/ALTAK-', '').split('/', 1)
            self._ak = parts[0]
            self._sk = parts[1] if len(parts) > 1 else secret_key
        else:
            self._ak = api_key
            self._sk = secret_key
        self._plugin_id = plugin_id or '57d4e765-8af5-4ec0-8f9b-47075ec349e0'
        self._ok: bool | None = None

    def _bce_sign(self, method: str, path: str, headers: dict, params: dict = None,
                   body: bytes = b'') -> dict:
        """BCE IAM v1 签名，返回带 Authorization 的 headers"""
        import hashlib, hmac
        from urllib.parse import urlencode, quote
        from datetime import datetime, timezone

        # 时间戳
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        expiration = 1800  # 30 分钟

        # 1. 生成 auth string 和 signing key
        auth_string = f'bce-auth-v1/{self._ak}/{timestamp}/{expiration}'
        signing_key = hmac.new(
            self._sk.encode('utf-8'),
            auth_string.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        # 2. 准备 headers
        all_headers = dict(headers)
        all_headers.setdefault('host', 'aip.baidubce.com')
        all_headers.setdefault('x-bce-date', timestamp)

        # 3. 规范 headers（排序、小写、去空格）
        sorted_headers = sorted(all_headers.items(), key=lambda x: x[0].lower())
        canonical_headers = '\n'.join(
            f'{k.lower().strip()}:{v.strip()}'
            for k, v in sorted_headers
        )
        signed_headers = ';'.join(k.lower().strip() for k, v in sorted_headers)

        # 4. 规范 query string
        canonical_query = ''
        if params:
            sorted_params = sorted(params.items(), key=lambda x: x[0])
            canonical_query = '&'.join(
                f'{quote(str(k), safe="")}={quote(str(v), safe="")}'
                for k, v in sorted_params
            )

        # 5. 规范 URI
        canonical_uri = quote(path, safe='/:~')

        # 6. 规范请求
        canonical_request = (
            f'{method.upper()}\n'
            f'{canonical_uri}\n'
            f'{canonical_query}\n'
            f'{canonical_headers}\n'
            f'{signed_headers}'
        )

        # 7. 签名
        string_to_sign = (
            f'{auth_string}\n'
            f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
        )
        signature = hmac.new(
            signing_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        # 8. 构建 Authorization header
        all_headers['Authorization'] = (
            f'bce-auth-v1/{self._ak}/{timestamp}/{expiration}/'
            f'{signed_headers}/{signature}'
        )
        return all_headers

    def available(self) -> bool:
        if self._ok is False:
            return False
        if not self._ak or not self._sk:
            logger.warning('Qianfan: missing access_key or secret_key')
            self._ok = False
            return False
        self._ok = True
        return True

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self.available():
            return []

        try:
            pid = self._plugin_id
            url = f'{self.PLUGIN_API}{pid}/'
            body = {'query': query, 'stream': False}
            body_bytes = json.dumps(body).encode('utf-8')

            # 生成 BCE IAM v1 签名 headers
            headers = self._bce_sign(
                method='POST',
                path=f'/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin/{pid}/',
                headers={'content-type': 'application/json'},
                body=body_bytes,
            )

            resp = httpx.post(
                url,
                headers=headers,
                content=body_bytes,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            # 千帆插件返回格式可能为 { "result": [...] } 或 { "results": [...] }
            raw_results = data.get('result') or data.get('results') or data.get('data') or []
            if isinstance(raw_results, dict):
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
