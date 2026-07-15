"""代码专家 Agent — 专门处理代码编写、Debug、架构设计等问题。"""

from app.agents.base import BaseAgent, AgentContext

CODE_SYSTEM_PROMPT = """你是一个资深软件架构师和代码专家。在回答代码相关问题时：

1. **先分析需求**：理解用户真正的需求，不要急着写代码
2. **给出完整代码**：代码必须完整、可运行，包含必要的 import
3. **解释关键点**：对关键逻辑、边界情况、可能的陷阱做说明
4. **考虑最佳实践**：错误处理、类型注解、性能优化、安全性
5. **多种方案**：如果合适，给出不同方案及其取舍

输出格式：代码用 Markdown 代码块标注语言，解释用自然语言。
"""


class CodeAgent(BaseAgent):
    name = 'code'
    label = '💻 代码专家'
    description = '编写代码、解释算法、设计架构、Debug 排查'
    system_prompt = CODE_SYSTEM_PROMPT
