"""质量审查 Agent — 评估最终回答的质量。"""

import json
import re

from app.agents.base import BaseAgent, AgentContext

REVIEWER_SYSTEM_PROMPT = """你是一个回答质量审查员。审查最终的回答并给出评分和改进建议。

评分维度（每项 1-10 分）：
1. **准确度**：回答是否准确、无误导信息
2. **完整性**：是否全面覆盖了用户问题的各个方面
3. **清晰度**：表达是否清晰、结构化、易于理解
4. **实用性**：答案是否具有实际可操作性

输出格式 — 必须是合法 JSON：
{
    "accuracy": 8,
    "completeness": 7,
    "clarity": 9,
    "usefulness": 8,
    "average": 8.0,
    "strengths": ["优点1", "优点2"],
    "improvements": ["改进建议1", "改进建议2"]
}
"""


class ReviewerAgent(BaseAgent):
    name = 'reviewer'
    label = '⭐ 质量审查'
    description = '对最终回答进行评分并提供改进建议'
    system_prompt = REVIEWER_SYSTEM_PROMPT

    def _build_user_message(self, ctx: AgentContext) -> str:
        # Reviewer 需要看到最终的回答
        final_answer = ctx.final_answer or ctx.history_context or ''
        if not final_answer:
            return f'## 用户提问\n{ctx.question}\n\n（最终回答为空，无法审查）'
        return (
            f'## 用户提问\n{ctx.question}\n\n'
            f'## AI 回答\n{final_answer}\n\n'
            f'## 任务\n请对上述回答进行质量评分。'
        )

    async def execute(self, ctx: AgentContext) -> str:
        """执行审查并返回格式化的评分结果。"""
        try:
            raw = await self.provider.complete(
                system_prompt=self.system_prompt,
                user_message=self._build_user_message(ctx),
                temperature=0.2,
            )
            return self._format_review(raw)
        except Exception as exc:
            return f'审查出错：{exc}'

    @staticmethod
    def _format_review(raw: str) -> str:
        """解析并格式化审查结果。"""
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not json_match:
            return '审查解析失败'

        try:
            data = json.loads(json_match.group())
            avg = data.get('average', 0)
            strengths = data.get('strengths', [])
            improvements = data.get('improvements', [])

            lines = [f'**综合评分：{avg}/10**']
            if strengths:
                lines.append(f'\n✅ 优点：\n' + '\n'.join(f'- {s}' for s in strengths))
            if improvements:
                lines.append(f'\n💡 改进建议：\n' + '\n'.join(f'- {i}' for i in improvements))

            return '\n'.join(lines)
        except (json.JSONDecodeError, KeyError):
            return '审查解析失败'
