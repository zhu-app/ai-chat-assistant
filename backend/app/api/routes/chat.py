import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from uuid import uuid4

from app.api.schemas.chat import ChatStreamRequest, EditMessageRequest, KnowledgeDocumentDto, RenameSessionRequest
from app.core.config import settings
from app.core.dependencies import get_chat_service, get_current_user, get_document_service, get_session_repository, get_session_service
from app.core.errors import AppError
from app.domain import SessionSettings
from app.prompt_templates import get_template, list_templates
from app.infrastructure.persistence.sqlite_session_repository import SqliteSessionRepository
from app.llm.streaming import event_stream
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService, DocumentValidationError
from app.services.session_service import SessionService

router = APIRouter(prefix='/api', tags=['chat'])


@router.get('/sessions')
def list_sessions(
    session_service: SessionService = Depends(get_session_service),
    user_id: str = Depends(get_current_user),
):
    return session_service.list_sessions(user_id=user_id)


@router.get('/sessions/search')
def search_sessions(
    q: str = '',
    session_service: SessionService = Depends(get_session_service),
    user_id: str = Depends(get_current_user),
):
    """搜索会话（按标题和消息内容匹配）。"""
    if not q.strip():
        return session_service.list_sessions(user_id=user_id)
    return session_service.search_sessions(q.strip(), user_id=user_id)


@router.post('/sessions')
def create_session(
    session_service: SessionService = Depends(get_session_service),
    user_id: str = Depends(get_current_user),
):
    return session_service.create_session(user_id=user_id)


@router.delete('/sessions/{session_id}', status_code=204)
def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
    user_id: str = Depends(get_current_user),
):
    try:
        session_service.delete_session(session_id, user_id=user_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.patch('/sessions/{session_id}')
def rename_session(
    session_id: str,
    payload: RenameSessionRequest,
    session_service: SessionService = Depends(get_session_service),
    user_id: str = Depends(get_current_user),
):
    try:
        session = session_service.rename_session(session_id, payload.title.strip(), user_id=user_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    if not session:
        raise HTTPException(status_code=400, detail='标题不能为空')
    return session


@router.get('/sessions/{session_id}/messages')
def list_messages(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
    user_id: str = Depends(get_current_user),
):
    try:
        return session_service.list_messages(session_id, user_id=user_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.patch('/sessions/{session_id}/messages/{message_id}')
def edit_message(
    session_id: str,
    message_id: str,
    payload: EditMessageRequest,
    session_service: SessionService = Depends(get_session_service),
    user_id: str = Depends(get_current_user),
):
    """编辑消息内容（仅限自己的消息）。"""
    try:
        session_service.require_session_owner(session_id, user_id)
        messages = session_service.list_messages(session_id, user_id=user_id)
        for msg in messages:
            if msg.id == message_id and msg.role == 'user':
                from app.infrastructure.persistence.sqlite_session_repository import SqliteSessionRepository
                repo = SqliteSessionRepository(settings.sqlite_path)
                repo.update_message_content(message_id, payload.content)
                return {'ok': True}
        raise HTTPException(status_code=404, detail='消息不存在或无权编辑')
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get('/documents', response_model=list[KnowledgeDocumentDto])
def list_documents(
    document_service: DocumentService = Depends(get_document_service),
    user_id: str = Depends(get_current_user),
):
    return document_service.list_documents(user_id=user_id)


@router.post('/documents', response_model=list[KnowledgeDocumentDto])
async def upload_documents(
    files: list[UploadFile] = File(...),
    document_service: DocumentService = Depends(get_document_service),
    user_id: str = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail='请至少上传一个文档')
    try:
        return await document_service.upload_documents(files, user_id=user_id)
    except DocumentValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete('/documents/{document_id}', status_code=204)
def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
    user_id: str = Depends(get_current_user),
):
    # 只允许删除自己的文档
    deleted = document_service.delete_document(document_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='文档不存在')
    # 如果文档存在但不属于自己，delete_document 返回 None


@router.post('/sessions/{session_id}/share')
def share_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
    session_repository: SqliteSessionRepository = Depends(get_session_repository),
    user_id: str = Depends(get_current_user),
):
    """生成对话分享链接。"""
    try:
        # 验证会话所有权
        session_service.require_session_owner(session_id, user_id)
        share_token = str(uuid4())
        # 创建 share_tokens 表（幂等）
        with session_repository._connect() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS share_tokens (
                token TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )''')
            conn.execute('INSERT OR REPLACE INTO share_tokens (token, session_id, created_at) VALUES (?, ?, datetime("now"))',
                         (share_token, session_id))
        return {'shareUrl': f'/share/{share_token}', 'token': share_token}
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get('/sessions/shared/{share_token}')
def get_shared_session(
    share_token: str,
):
    """获取分享的对话内容（无需登录）。"""
    db_path = settings.sqlite_path
    repo = SqliteSessionRepository(db_path)
    with repo._connect() as conn:
        row = conn.execute('SELECT session_id FROM share_tokens WHERE token = ?', (share_token,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='分享链接无效或已过期')
        session_id = row['session_id']
    # 直接通过 repository 获取会话和消息（无需登录），绕过 session_service 的权限检查
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='会话不存在')
    messages = repo.list_messages(session_id)
    return {
        'session': {'id': session.id, 'title': session.title},
        'messages': [{'role': m.role, 'content': m.content, 'createdAt': m.created_at} for m in messages],
    }


@router.get('/templates')
def api_list_templates():
    """列出所有 Prompt 模板。"""
    return list_templates()


@router.get('/templates/{template_id}')
def api_get_template(template_id: str):
    """获取单个模板详情（含 system_prompt）。"""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail='模板不存在')
    return {
        'id': template.id,
        'emoji': template.emoji,
        'title': template.title,
        'description': template.description,
        'systemPrompt': template.system_prompt,
        'suggestedMessage': template.suggested_message,
    }


@router.post('/chat/stream')
async def chat_stream(
    payload: ChatStreamRequest,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(get_current_user),
):
    settings = SessionSettings(
        model=payload.settings.model,
        temperature=payload.settings.temperature,
        system_prompt=payload.settings.systemPrompt,
        use_rag=payload.settings.useRag,
        document_ids=payload.settings.documentIds,
        enable_prompt_optimizer=payload.settings.enablePromptOptimizer,
        enable_agent_mode=payload.settings.enableAgentMode,
        enable_web_search=payload.settings.enableWebSearch,
    )
    try:
        stream = chat_service.stream_chat(payload.sessionId, payload.message, settings, user_id=user_id)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    async def _with_disconnect_check():
        try:
            async for event in stream:
                if await request.is_disconnected():
                    await stream.aclose()
                    return
                yield event
        except AppError as exc:
            yield {
                'type': 'error',
                'sessionId': payload.sessionId or '',
                'messageId': '',
                'meta': {'message': exc.detail, 'statusCode': exc.status_code},
            }
            return
        except (GeneratorExit, asyncio.CancelledError):
            await stream.aclose()
            raise

    return StreamingResponse(event_stream(_with_disconnect_check()), media_type='text/event-stream')