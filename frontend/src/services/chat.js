const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');
const authHeaders = () => {
    const token = (() => {
        try {
            const raw = localStorage.getItem('ai-chat-mvp:token');
            return raw ? JSON.parse(raw) : null;
        }
        catch {
            return null;
        }
    })();
    return token ? { Authorization: `Bearer ${token}` } : {};
};
const toSession = (item) => ({
    id: item.id,
    title: item.title,
    model: item.model || 'glm-4-flash',
    systemPrompt: item.system_prompt || '你是一个清晰、直接、可靠的中文 AI 助手。',
    temperature: item.temperature ?? 0.7,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
});
const toMessage = (item) => ({
    id: item.id,
    sessionId: item.session_id,
    role: item.role,
    content: item.content,
    status: item.status,
    createdAt: item.created_at,
});
const toDocument = (item) => ({
    id: item.id,
    filename: item.filename,
    contentType: item.content_type,
    status: item.status,
    createdAt: item.created_at,
});
const parseSseChunk = (chunk) => {
    const dataLine = chunk
        .split('\n')
        .find((line) => line.startsWith('data: '));
    if (!dataLine)
        return [];
    try {
        return [JSON.parse(dataLine.replace('data: ', ''))];
    }
    catch {
        return [];
    }
};
const fetchApi = async (url, options = {}) => {
    const headers = { ...authHeaders(), ...(options.headers || {}) };
    const response = await fetch(url, { ...options, headers });
    // 401 时清除 token，后续操作会跳转到登录页
    if (response.status === 401) {
        localStorage.removeItem('ai-chat-mvp:token');
        localStorage.removeItem('ai-chat-mvp:user');
        window.location.reload();
    }
    return response;
};
export const listSessions = async () => {
    const response = await fetchApi(`${API_BASE}/sessions`);
    if (!response.ok)
        throw new Error('会话列表加载失败');
    const data = (await response.json());
    return data.map(toSession);
};
export const createSession = async () => {
    const response = await fetchApi(`${API_BASE}/sessions`, { method: 'POST' });
    if (!response.ok)
        throw new Error('创建会话失败');
    return toSession((await response.json()));
};
export const renameSession = async (sessionId, title) => {
    const response = await fetchApi(`${API_BASE}/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
    });
    if (!response.ok)
        throw new Error('重命名会话失败');
    return toSession((await response.json()));
};
export const deleteSession = async (sessionId) => {
    const response = await fetchApi(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
    if (!response.ok && response.status !== 204)
        throw new Error('删除会话失败');
};
export const listMessages = async (sessionId) => {
    const response = await fetchApi(`${API_BASE}/sessions/${sessionId}/messages`);
    if (!response.ok)
        throw new Error('消息加载失败');
    const data = (await response.json());
    return data.map(toMessage);
};
export const listDocuments = async () => {
    const response = await fetchApi(`${API_BASE}/documents`);
    if (!response.ok)
        throw new Error('文档列表加载失败');
    const data = (await response.json());
    return data.map(toDocument);
};
export const uploadDocuments = async (files) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const response = await fetchApi(`${API_BASE}/documents`, {
        method: 'POST',
        body: formData,
    });
    if (!response.ok)
        throw new Error('文档上传失败');
    const data = (await response.json());
    return data.map(toDocument);
};
export const deleteDocument = async (documentId) => {
    const response = await fetchApi(`${API_BASE}/documents/${documentId}`, { method: 'DELETE' });
    if (!response.ok && response.status !== 204)
        throw new Error('文档删除失败');
};
export const streamChat = async (payload, handlers) => {
    const response = await fetchApi(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: handlers.signal,
    });
    if (!response.ok || !response.body) {
        throw new Error('流式请求失败');
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    while (true) {
        const { done, value } = await reader.read();
        if (done)
            break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop() ?? '';
        blocks.flatMap(parseSseChunk).forEach(handlers.onEvent);
    }
    if (buffer.trim()) {
        parseSseChunk(buffer).forEach(handlers.onEvent);
    }
};
