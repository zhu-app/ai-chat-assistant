"""内容合成 Agent — 将多个 Agent 的输出合成为最终回答（流式输出）。

注意：不使用 LangChain 的流式 API（连接不稳定），改用 complete() 完整获取后
由后端逐块吐出，保证合成阶段稳定可靠。
"""

import asyncio
import re
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

# 流式输出块大小：按段落/标题/列表等 Markdown 自然边界拆分
# 每块约 1-3 句话，保证 Markdown 语法不被切断
_MIN_CHUNK_SIZE = 30   # 最小块字符数
_MAX_CHUNK_SIZE = 120  # 最大块字符数


def _split_into_chunks(text: str) -> list[str]:
    """
    按 Markdown 自然边界拆分文本，保证：
    - 不切断 `# ` `**` ```` `- ` 等 Markdown 语法
    - 不切断完整句子
    - 每块大小适中（30-120 字符）
    """
    if not text:
        return ['']

    # 第一步：按自然段落拆分（连续两个换行 = 段落边界）
    paragraphs = re.split(r'\n\n+', text)
    chunks: list[str] = []
    buffer = ''

    for para in paragraphs:
        if not para.strip():
            continue

        # 如果单个段落很长，进一步按句子拆分
        if len(para) > _MAX_CHUNK_SIZE * 1.5:
            # 按句号/感叹号/问号/换行拆分（保留标点）
            sub_sentences = re.split(r'(?<=[。！？!?\n])\s*', para)
            for sub in sub_sentences:
                if not sub.strip():
                    continue
                if len(buffer) + len(sub) < _MAX_CHUNK_SIZE:
                    buffer += sub
                else:
                    if buffer:
                        chunks.append(buffer.strip())
                    buffer = sub
        else:
            # 短段落，尝试合并到上一个块
            if len(buffer) + len(para) < _MAX_CHUNK_SIZE and buffer:
                buffer += '\n\n' + para
            else:
                if buffer:
                    chunks.append(buffer.strip())
                buffer = para

    if buffer:
        chunks.append(buffer.strip())

    # 极端情况：还是太长时做硬拆分（保留 Markdown 语法完整性）
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > _MAX_CHUNK_SIZE * 2:
            # 尝试按行拆分
            lines = chunk.split('\n')
            line_buffer = ''
            for line in lines:
                if len(line_buffer) + len(line) + 1 < _MAX_CHUNK_SIZE:
                    line_buffer += ('\n' if line_buffer else '') + line
                else:
                    if line_buffer:
                        final_chunks.append(line_buffer)
                    line_buffer = line
            if line_buffer:
                final_chunks.append(line_buffer)
        else:
            final_chunks.append(chunk)

    return final_chunks


class WriterAgent:
    """内容合成 Agent — 使用 complete() + 后端拆分模拟流式输出。"""

    name = 'writer'
    label = '✍️ 内容合成'

    def __init__(self, provider: ChatProvider) -> None:
        self.provider = provider

    async def stream_synthesize(
        self,
        ctx: AgentContext,
        agent_outputs: dict[str, str],
    ) -> AsyncIterator[str]:
        """将各 Agent 输出合成为流式最终回答。"""
        # 构建输入（截断过长的 Agent 输出以防超长上下文）
        parts = [f'## 用户提问\n{ctx.question}']

        if ctx.history_context:
            parts.append(f'## 对话背景\n{ctx.history_context[:500]}')

        # 判断是否有其他 Agent 的输出
        has_agent_outputs = bool(agent_outputs)

        if has_agent_outputs:
            # 加入各 Agent 的输出（每个最多 2000 字，足以保留完整信息）
            agents_section = []
            for agent_name, output in agent_outputs.items():
                truncated = output[:2000] if len(output) > 2000 else output
                agents_section.append(f'### {agent_name}\n{truncated}')
            parts.append(f'## 各 Agent 协作输出\n' + '\n\n'.join(agents_section))
            parts.append('## 任务\n将上述各 Agent 的输出合成为一份面向用户的最终回答。')
            system_prompt = WRITER_SYSTEM_PROMPT
        else:
            # 没有其他 Agent 输出 → 直接回答（简单问题场景）
            parts.append('## 要求\n请直接回答用户的问题，内容丰富、结构清晰、不少于 500 字。')
            system_prompt = DIRECT_ANSWER_PROMPT

        user_message = '\n\n---\n\n'.join(parts)

        try:
            # 使用 complete() 完整获取，更稳定
            full_response = await self.provider.complete(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=ctx.temperature,
                model=ctx.model,
            )

            if not full_response:
                yield '[合成阶段：AI 返回为空]'
                return

            # 拆分为自然段落块模拟流式输出
            chunks = _split_into_chunks(full_response)
            for i, chunk in enumerate(chunks):
                yield chunk
                # 动态延迟：首块快出（15ms），后续块根据大小调整（20-40ms）
                delay = 0.015 if i == 0 else min(0.04, 0.015 + len(chunk) * 0.0002)
                await asyncio.sleep(delay)

        except Exception as exc:
            yield f'[合成阶段出错：{exc}]'
