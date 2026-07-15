"""
遥测系统 — Token 计数、成本估算、延迟追踪、质量自评。

这不是一个"调 API"的功能，而是需要深入理解 LLM 原理才能实现的工程：
  - Token 估算：中英文混合的分词近似算法
  - 成本计算：按模型定价表精确计算
  - 延迟追踪：首字延迟、生成速率、总耗时
  - 质量自评：用 LLM 评估 LLM 输出的质量
"""

import time
import re
import json
from typing import Any

# ── 模型定价表（美元/1K tokens） ──
MODEL_PRICING: dict[str, dict[str, float]] = {
    'glm-4-flash': {'input': 0.0001, 'output': 0.0001},
    'glm-4-plus': {'input': 0.005, 'output': 0.005},
    'glm-4-air': {'input': 0.001, 'output': 0.001},
    'glm-4-long': {'input': 0.001, 'output': 0.002},
    'glm-4v': {'input': 0.005, 'output': 0.005},
    'gpt-4o': {'input': 0.0025, 'output': 0.01},
    'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
    'deepseek-chat': {'input': 0.00014, 'output': 0.00028},
    # 默认
    'default': {'input': 0.001, 'output': 0.002},
}


class TokenCounter:
    """
    智能 Token 估算器。

    为什么不做简单的 len(text) / 2？
    - 中文约 1.5 字符/token
    - 英文约 0.75 词/token
    - 代码符号密集，需要特殊处理
    """

    # CJK 字符范围
    CJK_RANGE = re.compile(r'[一-鿿㐀-䶿豈-﫿]')
    # 英文单词
    EN_WORD = re.compile(r'[a-zA-Z0-9_\-]+')
    # 空白字符
    WHITESPACE = re.compile(r'\s+')

    @classmethod
    def estimate(cls, text: str) -> int:
        """
        估算文本的 token 数量。
        使用混合策略：中文字符级 + 英文词级 + 符号惩罚。
        """
        if not text:
            return 0

        cjk_chars = cls.CJK_RANGE.findall(text)
        en_words = cls.EN_WORD.findall(text)
        other_chars = len(text) - len(''.join(cjk_chars)) - len(''.join(en_words))

        # 中文：约 1.5 字符/token（实际 1.2-2.0，取 1.5 作为合理估算）
        cjk_tokens = len(cjk_chars) / 1.5
        # 英文：约 0.75 词/token（实际 0.6-1.0，取 0.75）
        en_tokens = len(en_words) * 0.75
        # 符号/空格/标点：约 2 字符/token
        symbol_tokens = other_chars / 2.0

        return max(1, int(cjk_tokens + en_tokens + symbol_tokens))

    @classmethod
    def estimate_messages(cls, messages: list[dict[str, str]]) -> int:
        """估算消息列表的总 token 数（含格式开销）。"""
        base = 3  # 基础格式开销
        for msg in messages:
            base += 3  # 每条消息的角色开销
            for key, value in msg.items():
                if isinstance(value, str):
                    base += cls.estimate(value)
        return base


class CostCalculator:
    """成本计算器 — 按模型定价表精确计算。"""

    @staticmethod
    def get_pricing(model: str) -> dict[str, float]:
        """获取模型的定价。"""
        # 模糊匹配
        for key in MODEL_PRICING:
            if key in model:
                return MODEL_PRICING[key]
        return MODEL_PRICING['default']

    @classmethod
    def calculate(cls, input_tokens: int, output_tokens: int, model: str) -> float:
        """计算预估成本（美元）。"""
        pricing = cls.get_pricing(model)
        cost = (input_tokens / 1000) * pricing['input'] + (output_tokens / 1000) * pricing['output']
        return round(cost, 6)


class LatencyTracker:
    """延迟追踪器 — 测量首字延迟、生成速率、总耗时。"""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.first_token_time: float | None = None
        self.end_time: float | None = None
        self.total_tokens: int = 0

    def start(self) -> None:
        self.start_time = time.monotonic()
        self.first_token_time = None
        self.end_time = None
        self.total_tokens = 0

    def record_token(self) -> None:
        """记录一个 token 的到达。"""
        if self.first_token_time is None:
            self.first_token_time = time.monotonic()
        self.total_tokens += 1

    def stop(self) -> None:
        self.end_time = time.monotonic()

    @property
    def first_token_latency_ms(self) -> float:
        if self.first_token_time and self.start_time:
            return round((self.first_token_time - self.start_time) * 1000, 1)
        return 0.0

    @property
    def total_duration_ms(self) -> float:
        end = self.end_time or time.monotonic()
        return round((end - self.start_time) * 1000, 1)

    @property
    def tokens_per_second(self) -> float:
        if self.total_tokens > 0 and self.total_duration_ms > 0:
            return round(self.total_tokens / (self.total_duration_ms / 1000), 1)
        return 0.0


class ResponseEvaluator:
    """
    响应质量自评系统。

    用 LLM 评价 LLM 的输出质量，覆盖 4 个维度：
    - 准确度（Accuracy）：回答是否准确、无幻觉
    - 完整性（Completeness）：是否全面覆盖问题
    - 清晰度（Clarity）：表达是否清晰、结构化
    - 实用性（Usefulness）：答案是否具有实际价值
    """

    EVALUATION_PROMPT = """你是一个回答质量评审专家。请评估以下 AI 回答的质量。

评估维度（每项 1-10 分）：
1. 准确度：回答是否准确、无误导信息
2. 完整性：是否全面覆盖了用户问题的各个方面
3. 清晰度：表达是否清晰、结构化、易于理解
4. 实用性：答案是否具有实际可操作性

输出格式（严格 JSON，不要其他内容）：
{"accuracy": 8, "completeness": 7, "clarity": 9, "usefulness": 8, "average": 8.0, "summary": "一句话总结"}

用户问题：{question}

AI 回答：{answer}"""

    def __init__(self, provider=None) -> None:
        self.provider = provider

    async def evaluate(
        self,
        question: str,
        answer: str,
        model: str = '',
    ) -> dict[str, Any]:
        """评估回答质量。"""
        if not self.provider or not answer:
            return {
                'accuracy': 0,
                'completeness': 0,
                'clarity': 0,
                'usefulness': 0,
                'average': 0,
                'summary': '评估不可用',
            }

        prompt = self.EVALUATION_PROMPT.format(question=question, answer=answer[:3000])

        try:
            raw = await self.provider.complete(
                system_prompt='你是一个 JSON 评审专家，只输出 JSON。',
                user_message=prompt,
                temperature=0.1,
                model=model,
            )
            return self._parse_evaluation(raw)
        except Exception:
            return {
                'accuracy': 0,
                'completeness': 0,
                'clarity': 0,
                'usefulness': 0,
                'average': 0,
                'summary': '评估暂不可用',
            }

    @staticmethod
    def _parse_evaluation(raw: str) -> dict[str, Any]:
        """解析 LLM 返回的 JSON 评价。"""
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not json_match:
            return {'accuracy': 0, 'completeness': 0, 'clarity': 0, 'usefulness': 0, 'average': 0, 'summary': ''}

        try:
            data = json.loads(json_match.group())
            return {
                'accuracy': min(10, max(1, int(data.get('accuracy', 0)))),
                'completeness': min(10, max(1, int(data.get('completeness', 0)))),
                'clarity': min(10, max(1, int(data.get('clarity', 0)))),
                'usefulness': min(10, max(1, int(data.get('usefulness', 0)))),
                'average': round(float(data.get('average', 0)), 1),
                'summary': str(data.get('summary', '')),
            }
        except (json.JSONDecodeError, ValueError, KeyError):
            return {'accuracy': 0, 'completeness': 0, 'clarity': 0, 'usefulness': 0, 'average': 0, 'summary': ''}
