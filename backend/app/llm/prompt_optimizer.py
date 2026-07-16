"""
Prompt 优化引擎

三层策略：
1. 结构化改写 — 将模糊提问转化为清晰、有层次的结构化提问
2. 上下文增强 — 从对话历史中提取关键背景信息，自动补全
3. 角色注入 — 根据问题类型自动匹配专家角色，提升回答质量

使用 LLM 自身能力做 zero-shot 改写，无需训练数据。
"""

import json
import re

from app.domain import ChatMessage
from app.llm.providers.base import ChatProvider

# ── 系统提示词：指导 LLM 如何优化用户提问 ──
OPTIMIZER_SYSTEM_PROMPT = """你是一个专业的 Prompt 工程师，任务是将用户的原始提问改写为更清晰、更结构化、更容易获得高质量回答的版本。

改写规则：
1. **结构化**：如果提问是模糊的一句话，将其拆解为背景说明 + 核心问题 + 期望输出格式
2. **角色注入**：根据问题领域，在开头注入合适的专家角色（如"请以资深 Python 架构师的角度回答"）
3. **上下文增强**：如果对话历史中有相关的上下文，在提问中补全缺失的关键信息
4. **输出约束**：明确期望的回答格式（列表 / 代码 / 分步骤 / 对比表格等）
5. **保持原意**：不要改变用户的真实意图，只是让它更清晰
6. **中文输出**：改写后的 prompt 仍使用中文
7. **简洁**：改写后的内容不要超过原始提问长度的 3 倍

输出格式要求 — 必须是合法 JSON：
{"optimized": "改写后的完整提示词", "strategies": ["使用了哪些策略"], "reason": "简短说明为什么这样改写"}

如果原始提问已经很清晰、不需要改写，直接返回：
{"optimized": "原始提问", "strategies": [], "reason": "原始提问已足够清晰，无需改写"}
"""

# ── 质量检测：判断是否需要优化 ──
_SHORT_THRESHOLD = 8  # 少于 8 字的提问大概率需要优化


def _extract_history_context(history: list[ChatMessage], max_messages: int = 6) -> str:
    """从最近的对话历史中提取关键上下文。"""
    recent = history[-max_messages:] if len(history) > max_messages else history
    if not recent:
        return '（无历史对话）'

    lines = []
    for msg in recent:
        role = '用户' if msg.role == 'user' else 'AI'
        content = msg.content[:200] if msg.content else ''
        if content:
            lines.append(f'[{role}] {content}')
    return '\n'.join(lines)


def _needs_optimization(user_message: str) -> bool:
    """智能判断是否值得做 LLM 优化（节省 API 调用）。

    优化判断原则：
    - 超短提问（<8字）→ 大概率模糊，需要优化
    - 纯祈使句（如"讲一下Python"、"介绍AI"）→ 虽然简短但明确，跳过优化
    - 复杂问题（有明确的结构化需求）→ 跳过优化（用户已想清楚）
    - 中间状态（8-20字，无结构）→ 需要优化
    """
    text = user_message.strip()

    # 超短大概率模糊
    if len(text) < _SHORT_THRESHOLD:
        return True

    # 如果已经包含明确的结构化标记（数字列表、对比词、问题词），跳过优化
    structured_patterns = [
        r'[1-9]\)', r'[1-9]\.',        # 数字列表
        r'对比|区别|优缺点|异同|vs|VS',  # 对比类
        r'步骤|流程|方法|方案|如何',     # 结构化请求
        r'为什么|怎么|怎样|哪些|多少',   # 具体问题词
    ]
    import re
    if any(re.search(p, text) for p in structured_patterns):
        return False

    # 没有标点、没有问号、没有换行 → 可能是随手打的
    if not any(ch in text for ch in '？?。.\n，,'):
        return True

    # 有标点但整体像随手输入（短且无问句特征）
    if len(text) < 20 and '?' not in text and '？' not in text:
        return True

    return False


class PromptOptimizer:
    """Prompt 优化引擎"""

    def __init__(self, provider: ChatProvider) -> None:
        self.provider = provider

    async def optimize(
        self,
        user_message: str,
        history: list[ChatMessage] | None = None,
    ) -> dict:
        """
        优化用户提问。

        返回:
            {
                "original": str,       # 原始提问
                "optimized": str,      # 优化后的提问
                "strategies": list[str], # 使用的策略
                "reason": str,         # 优化理由
                "skipped": bool,       # 是否跳过了优化
            }
        """
        # 不需要优化 → 直接返回
        if not _needs_optimization(user_message):
            return {
                'original': user_message,
                'optimized': user_message,
                'strategies': [],
                'reason': '提问已足够清晰，无需优化',
                'skipped': True,
            }

        # 构建 LLM 输入
        history_context = _extract_history_context(history or [])
        user_input = (
            f'## 对话历史\n{history_context}\n\n'
            f'## 用户原始提问\n{user_message}\n\n'
            f'请改写这个提问。'
        )

        try:
            raw = await self.provider.complete(
                system_prompt=OPTIMIZER_SYSTEM_PROMPT,
                user_message=user_input,
                temperature=0.3,  # 低温度 → 稳定输出
            )
            result = self._parse_optimizer_response(raw, user_message)
            return result
        except Exception:
            # 优化失败 → 降级为原始提问
            return {
                'original': user_message,
                'optimized': user_message,
                'strategies': [],
                'reason': '优化服务暂不可用',
                'skipped': True,
            }

    @staticmethod
    def _parse_optimizer_response(raw: str, original: str) -> dict:
        """解析 LLM 返回的 JSON，容错处理。"""
        # 尝试提取 JSON 块
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not json_match:
            return {
                'original': original,
                'optimized': original,
                'strategies': [],
                'reason': '优化解析失败，使用原始提问',
                'skipped': True,
            }

        try:
            data = json.loads(json_match.group())
            optimized = data.get('optimized', '').strip()
            if not optimized:
                optimized = original

            return {
                'original': original,
                'optimized': optimized,
                'strategies': data.get('strategies', []),
                'reason': data.get('reason', ''),
                'skipped': False,
            }
        except (json.JSONDecodeError, KeyError):
            return {
                'original': original,
                'optimized': original,
                'strategies': [],
                'reason': '优化解析失败，使用原始提问',
                'skipped': True,
            }
