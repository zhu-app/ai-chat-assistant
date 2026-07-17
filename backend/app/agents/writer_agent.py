"""内容合成 Agent — 将多个 Agent 的输出合成为最终回答（真正的流式输出）。

使用 LLM 的 astream 接口逐 token 产出，前端实时可见。
"""

from typing import AsyncIterator

from app.agents.base import AgentContext
from app.llm.providers.base import ChatProvider

WRITER_SYSTEM_PROMPT = """你是一个内容合成专家。你的任务是将多个协作 Agent 的输出整合为一份面向用户的最终回答。

合成原则：
1. **保持连贯**：将各 Agent 的输出有机融合，而不是简单拼接
2. **去除冗余**：避免重复内容，取各 Agent 输出的精华
3. **统一风格**：用一致的语言风格呈现（自然、专业、清晰）
4. **保持价值**：保留各 Agent 独有的价值点
5. **结构化呈现**：用 Markdown 组织内容，至少使用 ### 级标题，层次分明
6. **引用来源**：如果内容来自检索的文档，注明参考来源
7. **内容充实**：每个小节至少 3-5 句话，提供充分的细节和深度
"""

DIRECT_ANSWER_PROMPT = """你是一个知识渊博的 AI 助手。请直接回答用户的问题。

要求：
1. **内容丰富**：每个要点至少 3-5 句话，提供充分的细节
2. **结构清晰**：使用 Markdown 标题（###）组织内容，包含概述、详细说明、实例等
3. **深度足够**：不要停留在表面介绍，提供深入的分析和独到的见解
4. **完整全面**：覆盖问题的各个维度，不少于 500 字
5. **中文输出**：用自然流畅的中文撰写
"""


class WriterAgent:
    """内容合成 Agent — 使用 LLM 流式接口，逐 token 产出。"""

    name = 'writer'
    label = '✍️ 内容合成'

    def __init__(self, provider: ChatProvider) -> None:
        self.provider = provider

    async def stream_synthesize(
        self,
        ctx: AgentContext,
        agent_outputs: dict[str, str],
    ) -> AsyncIterator[str]:
        """将各 Agent 输出合成为流式最终回答（真正的逐 token 流式）。"""
        # 构建输入
        parts = [f'## 用户提问\n{ctx.question}']

        if ctx.history_context:
            parts.append(f'## 对话背景\n{ctx.history_context[:500]}')

        has_agent_outputs = bool(agent_outputs)

        if has_agent_outputs:
            agents_section = []
            for agent_name, output in agent_outputs.items():
                truncated = output[:2000] if len(output) > 2000 else output
                agents_section.append(f'### {agent_name}\n{truncated}')
            parts.append(f'## 各 Agent 协作输出\n' + '\n\n'.join(agents_section))
            parts.append('## 任务\n将上述各 Agent 的输出合成为一份面向用户的最终回答。')
            system_prompt = WRITER_SYSTEM_PROMPT
        else:
            parts.append('## 要求\n请直接回答用户的问题，内容丰富、结构清晰、不少于 500 字。')
            system_prompt = DIRECT_ANSWER_PROMPT

        user_message = '\n\n---\n\n'.join(parts)

        try:
            # 使用 stream_complete() 真正的逐 token 流式输出
            async for token in self.provider.stream_complete(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=ctx.temperature,
                model=ctx.model,
            ):
                yield token

        except Exception as exc:
            yield f'[合成阶段出错：{exc}]'
