"""
Agent 编排器 — 分析用户问题，生成执行计划。

编排器使用 LLM 判断用户问题属于哪种类型，决定需要调用哪些 Agent，
并分配子任务。支持以下 Agent 类型：
- search: 知识库检索
- analyst: 多角度分析
- code: 代码生成与解释
- writer: 最终合成输出
- reviewer: 质量审查
"""

import json
import re
from typing import AsyncIterator

from app.llm.providers.base import ChatProvider

ORCHESTRATOR_SYSTEM_PROMPT = """你是一个智能任务编排器。分析用户的问题，决定需要调用哪些 Agent 来协作完成回答。

可用的 Agent：
1. **search** — 知识库检索：当用户问题明确涉及文档/知识库内容时调用
2. **analyst** — 多角度分析：对复杂问题（技术选型、方案对比、利弊分析等）进行多维度拆解
3. **code** — 代码专家：当用户问代码编写、Debug、算法、架构设计时调用
4. **writer** — 内容合成：总是需要，负责将各 Agent 的输出合成为最终回答
5. **reviewer** — 质量审查：对重要/复杂问题的回答做质量审查（可选）

输出格式 — 必须是合法 JSON：
{
    "plan": [
        {"agent": "analyst", "task": "分析哪些技术方案"},
        {"agent": "code", "task": "给出代码示例"},
        {"agent": "writer", "task": "合成为结构化回答"}
    ],
    "reason": "简要说明为什么选择这些 Agent"
}

规则：
- 至少包含 writer
- 如果问题包含代码请求，必须包含 code
- 如果问题涉及对比、分析、决策，建议包含 analyst
- 如果启用了 RAG 且问题与文档相关，包含 search
- 不要让计划过于复杂，2-4 个 Agent 即可
- 用中文输出
"""


class AgentPlan:
    """编排器生成的执行计划。"""

    def __init__(self, steps: list[dict], reason: str = '') -> None:
        self.steps = steps  # [{"agent": "xxx", "task": "xxx"}, ...]
        self.reason = reason

    @property
    def agent_names(self) -> list[str]:
        return [step['agent'] for step in self.steps]

    def has_agent(self, name: str) -> bool:
        return name in self.agent_names


class Orchestrator:
    """任务编排器"""

    def __init__(self, provider: ChatProvider) -> None:
        self.provider = provider

    @staticmethod
    def _needs_web_search(question: str) -> bool:
        """判断问题是否需要联网搜索。"""
        keywords = [
            '天气', '新闻', '最新', '今天', '实时', '股价', '汇率',
            '比赛', '结果', '最近', '热映', '票房', '行情',
            '2025', '2026', '2027', 'current', 'latest', 'news',
            'today', 'weather', 'stock', 'price',
        ]
        q = question.lower()
        return any(k in q for k in keywords)

    async def plan(
        self,
        question: str,
        has_rag: bool = False,
        has_web_search: bool = False,
        history_context: str = '',
    ) -> AgentPlan:
        """分析问题并生成执行计划。"""
        # 简单问题不需要编排
        if self._is_simple_question(question):
            return AgentPlan(
                steps=[{'agent': 'writer', 'task': '直接回答用户问题'}],
                reason='简单问题，直接回答即可',
            )

        user_input = (
            f'## 用户提问\n{question}\n\n'
            f'## 历史上下文\n{history_context}\n\n'
            f'## RAG 状态\n{"已启用" if has_rag else "未启用"}\n\n'
            f'请生成执行计划。{"注意：RAG 已启用，可考虑使用 search Agent。" if has_rag else ""}'
        )

        try:
            raw = await self.provider.complete(
                system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
                user_message=user_input,
                temperature=0.3,
            )
            return self._parse_plan(raw, has_rag, has_web_search, question)
        except Exception:
            return AgentPlan(
                steps=[{'agent': 'writer', 'task': '回答用户问题'}],
                reason='编排服务降级，使用默认流程',
            )

    @staticmethod
    def _is_simple_question(question: str) -> bool:
        """判断是否简单问题（不需要编排，直接回答效果更好）。"""
        q = question.strip()

        # 超短
        if len(q) < 8:
            return True

        # 问候语
        if q.lower() in {'你好', 'hello', 'hi', '你好吗', '你是谁', 'help'}:
            return True

        # "介绍/讲一下/什么是" 类问题 → 直接回答质量更高，Agent 模式反而画蛇添足
        intro_patterns = [
            '讲一下', '讲一讲', '介绍', '介绍一下', '什么是', '啥是',
            '简述', '说说', '解释', '解释一下', '说明', '说明一下',
        ]
        for pattern in intro_patterns:
            if q.startswith(pattern) or q.startswith(pattern.lower()):
                return True

        return False

    @staticmethod
    def _parse_plan(raw: str, has_rag: bool, has_web_search: bool = False, question: str = '') -> AgentPlan:
        """解析编排器的 JSON 输出。"""
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not json_match:
            return AgentPlan(
                steps=[{'agent': 'writer', 'task': '回答用户问题'}],
                reason='解析失败，使用默认流程',
            )

        try:
            data = json.loads(json_match.group())
            plan = data.get('plan', [])
            reason = data.get('reason', '')

            if not isinstance(plan, list) or not plan:
                raise ValueError('Invalid plan')

            # 确保有 writer
            agent_names = [p['agent'] for p in plan if 'agent' in p]
            if 'writer' not in agent_names:
                plan.append({'agent': 'writer', 'task': '合成为最终回答'})

            # 如果 RAG 启用但计划中没有 search，且问题可能涉及知识，添加 search
            if has_rag and 'search' not in agent_names:
                plan.insert(0, {'agent': 'search', 'task': '检索相关文档知识'})

            # 如果联网搜索启用且问题需要实时信息，添加 web_search
            if has_web_search and Orchestrator._needs_web_search(question) and 'web_search' not in agent_names:
                plan.insert(0, {'agent': 'web_search', 'task': '搜索网络获取最新信息'})

            return AgentPlan(steps=plan, reason=reason)
        except (json.JSONDecodeError, ValueError, KeyError):
            return AgentPlan(
                steps=[{'agent': 'writer', 'task': '回答用户问题'}],
                reason='解析失败，使用默认流程',
            )
