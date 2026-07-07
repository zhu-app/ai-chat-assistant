from app.domain import SessionSettings


def build_chat_prompt(settings: SessionSettings, context_docs: list[str] | None = None) -> str:
    context_block = ''
    if context_docs:
        context_block = '\n\n'.join(context_docs)

    return '\n\n'.join(
        part for part in [
            settings.system_prompt,
            f'参考上下文：\n{context_block}' if context_block else '',
        ] if part
    )