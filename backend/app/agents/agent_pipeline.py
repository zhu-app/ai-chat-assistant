"""
Agent 流水线 — 统筹编排器的计划，并行执行 Agent，流式输出结果。

执行流程:
1. 编排器分析问题 → 生成执行计划
2. 非 writer Agent **并行执行**（search、analyst、code 等同时运行）
3. writer Agent 将所有输出合成为最终回答（真正流式）
4. reviewer Agent 可选审查最终回答质量
"""

import asyncio
from typing import AsyncIterator

from app.agents.analyst_agent import AnalystAgent
from app.agents.base import AgentContext
from app.agents.code_agent import CodeAgent
from app.agents.orchestrator import Orchestrator
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.search_agent import SearchAgent
from app.agents.web_search_agent import WebSearchAgent
from app.agents.writer_agent import WriterAgent
from app.domain import RetrievedChunk, SessionSettings
from app.llm.providers.base import ChatProvider
from app.repositories.retrieval_repository import RetrievalRepository


def _extract_history_text(history: list) -> str:
    """从对话历史中提取文本上下文。"""
    if not history:
        return ''
    lines = []
    for item in history:
        role = '用户' if item.role == 'user' else 'AI'
        content = (item.content or '')[:300]
        if content:
            lines.append(f'[{role}] {content}')
    return '\n'.join(lines[-6:])


class AgentPipeline:
    """Agent 流水线：编排 -> 并行执行 -> 合成 -> 审查"""

    def __init__(
        self,
        provider: ChatProvider,
        retriever: RetrievalRepository | None = None,
    ) -> None:
        self.provider = provider
        self.retriever = retriever
        self.orchestrator = Orchestrator(provider)
        self.search_agent = SearchAgent(provider)
        self.analyst_agent = AnalystAgent(provider)
        self.code_agent = CodeAgent(provider)
        self.writer_agent = WriterAgent(provider)
        self.reviewer_agent = ReviewerAgent(provider)
        self.web_search_agent = WebSearchAgent(provider)
        self._agent_map = {
            'search': self.search_agent,
            'analyst': self.analyst_agent,
            'code': self.code_agent,
            'reviewer': self.reviewer_agent,
            'web_search': self.web_search_agent,
        }

    async def stream_execute(
        self,
        question: str,
        settings: SessionSettings,
        history: list | None = None,
    ) -> AsyncIterator[dict]:
        """执行完整的 Agent 流水线，流式输出 SSE 事件。"""
        history_text = _extract_history_text(history or [])

        # 1. 编排阶段
        plan = await self.orchestrator.plan(
            question=question,
            has_rag=settings.use_rag and bool(settings.document_ids),
            has_web_search=settings.enable_web_search,
            history_context=history_text,
        )
        yield {
            'type': 'agent_plan',
            'meta': {
                'steps': [{'agent': s['agent'], 'task': s['task']} for s in plan.steps],
                'reason': plan.reason,
            },
        }

        # 2. 检索阶段（与 Agent 执行解耦，提前完成）
        retrieved_chunks: list[RetrievedChunk] = []
        if settings.use_rag and self.retriever and settings.document_ids:
            retrieved_chunks = self.retriever.retrieve(question, settings.document_ids)

        ctx = AgentContext(
            question=question,
            history_context=history_text,
            retrieved_chunks=retrieved_chunks,
            temperature=settings.temperature,
            model=settings.model,
        )

        # 3. 并行执行所有非 writer Agent
        execution_agents = [s for s in plan.steps if s['agent'] != 'writer']

        # 先发送所有 start 事件
        for step in execution_agents:
            agent_name = step['agent']
            agent = self._agent_map.get(agent_name)
            yield {
                'type': 'agent_step_start',
                'meta': {
                    'agent': agent_name,
                    'label': getattr(agent, 'label', agent_name) if agent else agent_name,
                    'task': step.get('task', ''),
                },
            }

        # 并行执行所有 Agent
        async def _run_agent(step: dict):
            agent_name = step['agent']
            agent = self._agent_map.get(agent_name)
            if not agent:
                return agent_name, f'Agent "{agent_name}" 未注册', True
            try:
                result = await agent.execute(ctx)
                return agent_name, result, False
            except Exception as exc:
                return agent_name, f'执行出错：{exc}', True

        agent_results = await asyncio.gather(
            *[_run_agent(step) for step in execution_agents],
            return_exceptions=False,
        )

        # 收集结果 + 发送 done 事件
        agent_outputs: dict[str, str] = {}
        for agent_name, result, is_error in agent_results:
            agent_outputs[agent_name] = result
            agent = self._agent_map.get(agent_name)
            yield {
                'type': 'agent_step_done',
                'meta': {
                    'agent': agent_name,
                    'label': getattr(agent, 'label', agent_name) if agent else agent_name,
                    'summary': ('❌ ' if is_error else '✅ ') + (result[:200] if result else '空输出'),
                },
            }

        # 4. 合成阶段（真正的流式输出）
        yield {
            'type': 'agent_step_start',
            'meta': {
                'agent': 'writer',
                'label': '合成最终回答',
                'task': '将所有 Agent 输出整合为最终回答',
            },
        }

        full_response = ''
        try:
            async for token in self.writer_agent.stream_synthesize(ctx, agent_outputs):
                full_response += token
                yield {
                    'type': 'token',
                    'delta': token,
                }
        except Exception as exc:
            error_text = f'[合成过程出错：{exc}]'
            full_response = error_text
            yield {
                'type': 'token',
                'delta': error_text,
            }

        yield {
            'type': 'agent_step_done',
            'meta': {
                'agent': 'writer',
                'label': '合成最终回答',
                'summary': f'已完成合成，共 {len(full_response)} 字符',
            },
        }

        yield {
            'type': 'agent_synthesized',
            'meta': {
                'full_response': full_response,
            },
        }

        # 5. 审查阶段（可选）
        if plan.has_agent('reviewer'):
            review_ctx = AgentContext(
                question=question,
                history_context=history_text,
                final_answer=full_response,
                temperature=0.2,
                model=settings.model,
            )
            try:
                review_result = await self.reviewer_agent.execute(review_ctx)
                yield {
                    'type': 'agent_review',
                    'meta': {
                        'review': review_result,
                    },
                }
            except Exception:
                pass  # 审查失败不影响主流程
