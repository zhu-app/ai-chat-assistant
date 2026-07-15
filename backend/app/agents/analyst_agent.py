"""多角度分析 Agent — 对复杂问题进行多维度拆解分析。"""

from app.agents.base import BaseAgent, AgentContext

ANALYST_SYSTEM_PROMPT = """你是一个资深分析专家。请从以下多个维度对用户的问题进行系统分析：

1. **背景与现状**：这个问题的背景是什么？当前面临什么情况？
2. **可选方案**：有哪些可能的解决方案或思路？
3. **利弊对比**：每种方案的优缺点、适用场景
4. **推荐建议**：基于分析给出明确的推荐

输出格式：使用 Markdown 结构，每个维度作为一级标题，内容简洁有力。
"""


class AnalystAgent(BaseAgent):
    name = 'analyst'
    label = '🔍 深度分析'
    description = '从多个维度（背景、方案、利弊、建议）对复杂问题进行全面分析'
    system_prompt = ANALYST_SYSTEM_PROMPT
