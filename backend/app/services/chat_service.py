import asyncio
from typing import AsyncIterator

from app.core.config import settings as app_settings
from app.core.telemetry import CostCalculator, LatencyTracker, TokenCounter
from app.domain import ChatMessage, RetrievedChunk, SessionSettings
from app.llm.providers.base import ChatProvider
from app.repositories.retrieval_repository import RetrievalRepository
from app.repositories.session_repository import SessionRepository
from app.services.session_service import SessionService

# 单次 token 流超时（秒），防止 LLM 挂死
_TOKEN_TIMEOUT = 120.0

# ── 对话自动命名 ──

# 对话标题中需要去除的常见前缀
_TITLE_PREFIXES = [
    '讲一下', '讲一讲', '介绍一下', '什么是', '请帮我', '帮我',
    '请问', '你好', 'hi', 'hello', '你好，', '你好,',
]

# 最佳标题长度
_TITLE_MAX_LENGTH = 30
_TITLE_MIN_LENGTH = 4


def _clean_title(user_message: str) -> str:
    """从用户第一条消息生成干净的对话标题。"""
    text = user_message.strip()

    # 去除常见前缀 + 开头标点（循环直到没有匹配）
    changed = True
    while changed:
        changed = False
        # 先去开头标点
        text = text.lstrip('，。！？,。!?；;、：: ')
        for prefix in _TITLE_PREFIXES:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
                changed = True
                break

    # 截断到最大长度，在最后一个空格/标点处断句
    if len(text) > _TITLE_MAX_LENGTH:
        truncated = text[:_TITLE_MAX_LENGTH]
        # 只在截断位置附近（最后8字内）找标点断句，避免过早截断
        punct_pos = -1
        for ch in ('，', '。', '；', '、', ',', '.', ';', ' '):
            pos = truncated.rfind(ch, _TITLE_MAX_LENGTH - 8, _TITLE_MAX_LENGTH)
            if pos > punct_pos:
                punct_pos = pos
        if punct_pos > _TITLE_MIN_LENGTH:
            text = truncated[:punct_pos]
        else:
            text = truncated

    # 如果太短就返回原始文本
    result = text.strip() or user_message[:_TITLE_MAX_LENGTH].strip()
    return result if result else '新对话'


class ChatService:
    def __init__(
        self,
        session_service: SessionService,
        session_repository: SessionRepository,
        provider: ChatProvider,
        retriever: RetrievalRepository,
        prompt_optimizer=None,
        agent_pipeline=None,
        response_evaluator=None,
    ) -> None:
        self.session_service = session_service
        self.session_repository = session_repository
        self.provider = provider
        self.retriever = retriever
        self.prompt_optimizer = prompt_optimizer
        self.agent_pipeline = agent_pipeline
        self.response_evaluator = response_evaluator

    @staticmethod
    async def _timeout_stream(stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """为每个 token 添加超时保护，防止 LLM 挂死"""
        try:
            while True:
                token = await asyncio.wait_for(stream.__anext__(), timeout=_TOKEN_TIMEOUT)
                yield token
        except asyncio.TimeoutError:
            raise TimeoutError('LLM 响应超时，请重试') from None
        except StopAsyncIteration:
            return

    @staticmethod
    def _format_context_docs(chunks: list[RetrievedChunk]) -> list[str]:
        return [f'[{chunk.filename}]\n{chunk.content}' for chunk in chunks]

    @staticmethod
    def _format_sources(chunks: list[RetrievedChunk]) -> list[dict]:
        return [
            {
                'documentId': chunk.document_id,
                'filename': chunk.filename,
                'score': chunk.score,
                'chunkIndex': chunk.chunk_index,
                'preview': chunk.content[:180],
            }
            for chunk in chunks
        ]

    async def stream_chat(
        self,
        session_id: str | None,
        user_message: str,
        settings: SessionSettings,
        user_id: str = '',
    ) -> AsyncIterator[dict]:
        session = self.session_service.get_or_create_session(session_id, settings, user_id=user_id)

        # 全局 RAG 开关：后端可强制禁用 RAG
        if not app_settings.enable_rag:
            settings.use_rag = False

        # ── 阶段 0：Prompt 优化（可选） ──
        if settings.enable_prompt_optimizer and self.prompt_optimizer:
            history = self.session_repository.list_messages(session.id)
            opt_result = await self.prompt_optimizer.optimize(user_message, history)
            if not opt_result['skipped'] and opt_result['optimized'] != user_message:
                user_message = opt_result['optimized']
                yield {
                    'type': 'prompt_optimized',
                    'sessionId': session.id,
                    'meta': {
                        'original': opt_result['original'],
                        'optimized': opt_result['optimized'],
                        'strategies': opt_result['strategies'],
                        'reason': opt_result['reason'],
                    },
                }

        # ── 阶段 1：Agent 模式（可选） ──
        if settings.enable_agent_mode and self.agent_pipeline:
            # Agent 模式下，由 AgentPipeline 管理整个流程
            yield {
                'type': 'message_started',
                'sessionId': session.id,
                'messageId': '',
            }

            # 更新会话元数据
            title = _clean_title(user_message) or '新对话'
            self.session_repository.touch_session(
                session.id,
                title=title if session.title == '新对话' else None,
                temperature=settings.temperature,
            )

            # 保存用户消息
            user_entry = ChatMessage(
                session_id=session.id, role='user', content=user_message, status='done'
            )
            self.session_repository.save_message(user_entry)

            # 保存 assistant 占位
            assistant_entry = ChatMessage(
                session_id=session.id, role='assistant', content='', status='streaming'
            )
            # 先把 assistant 消息保存到数据库（获取真实 id）
            self.session_repository.save_message(assistant_entry)

            yield {
                'type': 'session_created',
                'sessionId': session.id,
                'meta': {
                    'title': self.session_repository.get_session(session.id).title,
                    'temperature': session.temperature,
                },
            }

            history = self.session_repository.list_messages(session.id)

            # 执行 Agent 流水线
            full_response = ''
            try:
                async for event in self.agent_pipeline.stream_execute(
                    question=user_message,
                    settings=settings,
                    history=history,
                ):
                    event['sessionId'] = session.id
                    event['messageId'] = assistant_entry.id

                    # 收集 token
                    if event['type'] == 'token':
                        assistant_entry.content += event.get('delta', '')
                        full_response += event.get('delta', '')
                    elif event['type'] == 'agent_synthesized':
                        full_response = event['meta'].get('full_response', '')
                        continue  # 不直接透传此事件给前端

                    # 透传所有事件到前端
                    yield event

            except Exception as exc:
                assistant_entry.status = 'error'
                self.session_repository.save_message(assistant_entry)
                yield {
                    'type': 'error',
                    'sessionId': session.id,
                    'messageId': assistant_entry.id,
                    'meta': {'message': str(exc)},
                }
                return

            # 完成
            assistant_entry.content = full_response or assistant_entry.content
            assistant_entry.status = 'done'
            self.session_repository.save_message(assistant_entry)

            # 获取检索来源
            retrieved_chunks = (
                self.retriever.retrieve(user_message, settings.document_ids)
                if settings.use_rag
                else []
            )

            yield {
                'type': 'message_done',
                'sessionId': session.id,
                'messageId': assistant_entry.id,
                'meta': {
                    'content': assistant_entry.content,
                    'sources': self._format_sources(retrieved_chunks),
                },
            }
            return

        # ── 阶段 2：普通模式（原有逻辑 + Prompt 优化支持 + 遥测追踪） ──
        title = _clean_title(user_message) or '新对话'
        self.session_repository.touch_session(
            session.id,
            title=title if session.title == '新对话' else None,
            temperature=settings.temperature,
        )

        user_entry = ChatMessage(session_id=session.id, role='user', content=user_message, status='done')
        self.session_repository.save_message(user_entry)

        assistant_entry = ChatMessage(session_id=session.id, role='assistant', content='', status='streaming')

        yield {
            'type': 'session_created',
            'sessionId': session.id,
            'meta': {
                'title': self.session_repository.get_session(session.id).title,
                'temperature': session.temperature,
            },
        }
        yield {
            'type': 'message_started',
            'sessionId': session.id,
            'messageId': assistant_entry.id,
        }

        history = self.session_repository.list_messages(session.id)
        retrieved_chunks = self.retriever.retrieve(user_message, settings.document_ids) if settings.use_rag else []
        context_docs = self._format_context_docs(retrieved_chunks)

        # ── 联网搜索（普通模式也支持） ──
        if settings.enable_web_search:
            try:
                from app.tools.web_search import WebSearchTool
                # 根据后端类型选择对应 API Key
                if app_settings.search_backend == 'qianfan':
                    search_api_key = app_settings.qianfan_api_key
                    search_secret_key = app_settings.qianfan_secret_key
                    search_plugin_id = app_settings.qianfan_plugin_id
                elif app_settings.search_backend == 'bing':
                    search_api_key = app_settings.bing_api_key
                    search_secret_key = ''
                    search_plugin_id = ''
                else:
                    search_api_key = ''
                    search_secret_key = ''
                    search_plugin_id = ''

                web_search = WebSearchTool(
                    backend_name=app_settings.search_backend,
                    api_key=search_api_key,
                    secret_key=search_secret_key,
                    plugin_id=search_plugin_id,
                )
                web_results = web_search.search_formatted(user_message)
                if web_results and not web_results.startswith('〈'):
                    context_docs = [*context_docs, web_results]
            except Exception:
                pass  # 搜索失败不影响主流程

        # ── 遥测追踪 ──
        latency = LatencyTracker()
        latency.start()
        input_text = user_message + '\n'.join(context_docs)
        input_tokens = TokenCounter.estimate(input_text)

        # 发送遥测初始化事件
        yield {
            'type': 'telemetry',
            'sessionId': session.id,
            'messageId': assistant_entry.id,
            'meta': {
                'phase': 'start',
                'inputTokens': input_tokens,
                'model': settings.model,
            },
        }

        try:
            async for token in self._timeout_stream(
                self.provider.stream_reply(history, settings, context_docs)
            ):
                assistant_entry.content += token
                latency.record_token()
                yield {
                    'type': 'token',
                    'sessionId': session.id,
                    'messageId': assistant_entry.id,
                    'delta': token,
                }
        except asyncio.CancelledError:
            assistant_entry.status = 'aborted'
            self.session_repository.save_message(assistant_entry)
            return
        except GeneratorExit:
            assistant_entry.status = 'aborted'
            self.session_repository.save_message(assistant_entry)
            return
        except Exception as exc:
            assistant_entry.status = 'error'
            self.session_repository.save_message(assistant_entry)
            yield {
                'type': 'error',
                'sessionId': session.id,
                'messageId': assistant_entry.id,
                'meta': {'message': str(exc)},
            }
            return

        latency.stop()
        assistant_entry.status = 'done'
        self.session_repository.save_message(assistant_entry)

        # ── 计算遥测数据 ──
        output_tokens = TokenCounter.estimate(assistant_entry.content)
        cost = CostCalculator.calculate(input_tokens, output_tokens, settings.model)

        # 质量自评（异步，不阻塞主流程）
        quality_score = 0.0
        quality_details = {}
        if self.response_evaluator and assistant_entry.content:
            try:
                eval_result = await self.response_evaluator.evaluate(
                    question=user_message,
                    answer=assistant_entry.content,
                    model=settings.model,
                )
                quality_score = eval_result.get('average', 0.0)
                quality_details = {
                    'accuracy': eval_result.get('accuracy', 0),
                    'completeness': eval_result.get('completeness', 0),
                    'clarity': eval_result.get('clarity', 0),
                    'usefulness': eval_result.get('usefulness', 0),
                    'summary': eval_result.get('summary', ''),
                }
            except Exception:
                pass

        # 构建遥测事件
        telemetry_data = {
            'firstTokenLatencyMs': latency.first_token_latency_ms,
            'totalDurationMs': latency.total_duration_ms,
            'tokensPerSecond': latency.tokens_per_second,
            'inputTokens': input_tokens,
            'outputTokens': output_tokens,
            'estimatedCostUsd': cost,
            'ragChunksRetrieved': len(retrieved_chunks),
            'ragTopScore': round(max((c.score for c in retrieved_chunks), default=0.0), 2),
            'qualityScore': quality_score,
            'qualityDetails': quality_details,
        }

        yield {
            'type': 'message_done',
            'sessionId': session.id,
            'messageId': assistant_entry.id,
            'meta': {
                'content': assistant_entry.content,
                'sources': self._format_sources(retrieved_chunks),
                'telemetry': telemetry_data,
            },
        }
        # 额外发送遥测事件（前端可单独处理）
        yield {
            'type': 'telemetry',
            'sessionId': session.id,
            'messageId': assistant_entry.id,
            'meta': {
                'phase': 'done',
                **telemetry_data,
            },
        }