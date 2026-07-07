from app.core.config import settings as app_settings
from app.domain import ChatMessage, SessionSettings
from app.llm.providers.base import ChatProvider

if app_settings.openai_api_key:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI


    def build_messages(
        history: list[ChatMessage],
        settings: SessionSettings,
        context_docs: list[str] | None = None,
    ):
        messages = [SystemMessage(content=settings.system_prompt)]

        if context_docs:
            context = '\n\n'.join(context_docs)
            messages.append(
                SystemMessage(
                    content=(
                        '以下内容是已经从用户当前选中文档中检索出的参考片段。'
                        '回答时请直接基于这些内容进行自然、简洁、面向用户的说明。'
                        '不要提“当前命中的文档片段”“我无法访问文档”这类实现细节；'
                        '如果信息不足，只需说明“这份文档当前提供的信息有限”。\n'
                        f'{context}'
                    )
                )
            )

        for item in history:
            if item.role == 'user':
                messages.append(HumanMessage(content=item.content))
            elif item.role == 'assistant':
                messages.append(AIMessage(content=item.content))
            else:
                messages.append(SystemMessage(content=item.content))

        return messages


class OpenAICompatibleChatProvider(ChatProvider):
    def __init__(self) -> None:
        self.default_model = app_settings.openai_model
        self.has_remote_model = bool(app_settings.openai_api_key)
        self.client = None
        if self.has_remote_model:
            self.client = ChatOpenAI(
                api_key=app_settings.openai_api_key,
                model=app_settings.openai_model,
                base_url=app_settings.openai_base_url,
                temperature=0.7,
                streaming=True,
                timeout=60,
                max_retries=2,
            )

    async def _mock_stream(self, history: list[ChatMessage], context_docs: list[str] | None = None):
        latest_user = next((item.content for item in reversed(history) if item.role == 'user'), '')
        prefix = '本地模拟回复已启用。'
        if context_docs:
            prefix += f' 已命中 {len(context_docs)} 段知识库内容。'
        reply = f'{prefix}\n\n你刚刚说的是：{latest_user}'
        for part in reply.split(' '):
            yield f'{part} '

    async def stream_reply(self, history: list[ChatMessage], settings: SessionSettings, context_docs: list[str] | None = None):
        if not self.has_remote_model or not self.client:
            async for token in self._mock_stream(history, context_docs):
                yield token
            return

        client = self.client.bind(
            model=settings.model or self.default_model,
            temperature=settings.temperature,
        )
        messages = build_messages(history, settings, context_docs)
        async for chunk in client.astream(messages):
            text = getattr(chunk, 'content', '')
            if isinstance(text, list):
                text = ''.join(str(part) for part in text)
            if text:
                yield str(text)