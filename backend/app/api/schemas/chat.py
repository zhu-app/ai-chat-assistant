from pydantic import BaseModel, Field


class SessionSettingsDto(BaseModel):
    model: str = Field(default='glm-4-flash')
    temperature: float = Field(default=0.7)
    systemPrompt: str = Field(default='你是一个清晰、直接、可靠的中文 AI 助手。')
    useRag: bool = Field(default=False)
    documentIds: list[str] = Field(default_factory=list)
    enablePromptOptimizer: bool = Field(default=False)
    enableAgentMode: bool = Field(default=False)
    enableWebSearch: bool = Field(default=False)


class RenameSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class ChatStreamRequest(BaseModel):
    sessionId: str | None = None
    message: str
    settings: SessionSettingsDto = Field(default_factory=SessionSettingsDto)


class KnowledgeDocumentDto(BaseModel):
    id: str
    filename: str
    content_type: str
    status: str
    created_at: str