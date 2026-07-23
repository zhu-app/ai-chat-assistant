from dataclasses import dataclass, replace

from app.core.telemetry import TokenCounter
from app.domain import ChatMessage


@dataclass(frozen=True)
class ContextWindow:
    messages: list[ChatMessage]
    original_count: int
    omitted_count: int
    estimated_tokens: int


def _message_tokens(message: ChatMessage) -> int:
    return TokenCounter.estimate(message.content) + 4


def _build_extract_summary(messages: list[ChatMessage], max_tokens: int) -> str:
    if not messages or max_tokens <= 0:
        return ''

    lines: list[str] = []
    used_tokens = TokenCounter.estimate('Earlier conversation summary:')
    for message in reversed(messages):
        compact = ' '.join(message.content.split())
        if not compact:
            continue
        excerpt = compact[:240]
        line = f'- {message.role}: {excerpt}'
        line_tokens = TokenCounter.estimate(line)
        if lines and used_tokens + line_tokens > max_tokens:
            break
        if not lines and used_tokens + line_tokens > max_tokens:
            excerpt = excerpt[: max(40, max_tokens * 2)]
            line = f'- {message.role}: {excerpt}'
        lines.append(line)
        used_tokens += TokenCounter.estimate(line)

    lines.reverse()
    return 'Earlier conversation summary:\n' + '\n'.join(lines) if lines else ''


def _truncate_message(message: ChatMessage, max_tokens: int) -> ChatMessage:
    if _message_tokens(message) <= max_tokens:
        return message

    marker = '\n[...content truncated...]\n'
    low = 0
    high = len(message.content)
    best = ''
    while low <= high:
        keep = (low + high) // 2
        head_length = (keep + 1) // 2
        tail_length = keep // 2
        candidate = (
            message.content[:head_length]
            + marker
            + (message.content[-tail_length:] if tail_length else '')
        )
        if TokenCounter.estimate(candidate) + 4 <= max_tokens:
            best = candidate
            low = keep + 1
        else:
            high = keep - 1
    return replace(message, content=best or message.content[: max(max_tokens, 1)])


def build_context_window(
    messages: list[ChatMessage],
    max_tokens: int,
    recent_message_limit: int,
    summary_max_tokens: int,
) -> ContextWindow:
    usable = [
        message
        for message in messages
        if message.content.strip() and message.status not in {'error', 'aborted'}
    ]
    original_count = len(usable)
    budget = max(max_tokens, 256)
    total_tokens = sum(_message_tokens(message) for message in usable)
    if total_tokens <= budget:
        return ContextWindow(usable, original_count, 0, total_tokens)

    recent_limit = max(recent_message_limit, 2)
    split_at = max(0, len(usable) - recent_limit)
    older = list(usable[:split_at])
    recent = list(usable[split_at:])
    summary_budget = min(max(summary_max_tokens, 0), budget // 3)

    while len(recent) > 1 and sum(_message_tokens(message) for message in recent) > budget - summary_budget:
        older.append(recent.pop(0))

    summary_text = _build_extract_summary(older, summary_budget)
    result: list[ChatMessage] = []
    if summary_text:
        result.append(
            ChatMessage(
                session_id=recent[-1].session_id if recent else '',
                role='system',
                content=summary_text,
            )
        )
    result.extend(recent)

    has_summary = bool(summary_text and result and result[0].role == 'system')
    minimum_messages = 2 if has_summary else 1
    while len(result) > minimum_messages and sum(_message_tokens(message) for message in result) > budget:
        result.pop(1 if has_summary else 0)

    if has_summary and sum(_message_tokens(message) for message in result) > budget:
        result.pop(0)
        has_summary = False

    while len(result) > 1 and sum(_message_tokens(message) for message in result) > budget:
        result.pop(0)

    if result and sum(_message_tokens(message) for message in result) > budget:
        result[0] = _truncate_message(result[0], budget)

    estimated_tokens = sum(_message_tokens(message) for message in result)
    included_original = len(result) - (1 if has_summary else 0)
    return ContextWindow(
        messages=result,
        original_count=original_count,
        omitted_count=max(original_count - included_original, 0),
        estimated_tokens=estimated_tokens,
    )
