import type {
  ChatMessage,
  ChatSession,
  KnowledgeDocument,
  StreamEvent,
  StreamRequest,
} from '../types/chat';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

const authHeaders = (): Record<string, string> => {
  const token = (() => {
    try {
      const raw = localStorage.getItem('ai-chat-mvp:token');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  })();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

type ApiSession = {
  id: string;
  title: string;
  model: string;
  system_prompt: string;
  temperature: number;
  created_at: string;
  updated_at: string;
};

type ApiMessage = {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  status: 'pending' | 'streaming' | 'done' | 'error' | 'aborted';
  created_at: string;
};

type ApiDocument = {
  id: string;
  filename: string;
  content_type: string;
  status: string;
  created_at: string;
};

const toSession = (item: ApiSession): ChatSession => ({
  id: item.id,
  title: item.title,
  model: item.model || 'glm-4-flash',
  systemPrompt: item.system_prompt || '你是一个清晰、直接、可靠的中文 AI 助手。',
  temperature: item.temperature ?? 0.7,
  createdAt: item.created_at,
  updatedAt: item.updated_at,
});

const toMessage = (item: ApiMessage): ChatMessage => ({
  id: item.id,
  sessionId: item.session_id,
  role: item.role,
  content: item.content,
  status: item.status,
  createdAt: item.created_at,
});

const toDocument = (item: ApiDocument): KnowledgeDocument => ({
  id: item.id,
  filename: item.filename,
  contentType: item.content_type,
  status: item.status,
  createdAt: item.created_at,
});

const parseSseChunk = (chunk: string): StreamEvent[] => {
  const dataLine = chunk
    .split('\n')
    .find((line) => line.startsWith('data: '));

  if (!dataLine) return [];

  try {
    return [JSON.parse(dataLine.replace('data: ', '')) as StreamEvent];
  } catch {
    return [];
  }
};

const fetchApi = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const headers = { ...authHeaders(), ...(options.headers as Record<string, string> || {}) };
  const response = await fetch(url, { ...options, headers });
  // 401 时清除 token，但不刷新页面（避免无限刷新循环）
  if (response.status === 401) {
    localStorage.removeItem('ai-chat-mvp:token');
    localStorage.removeItem('ai-chat-mvp:user');
  }
  return response;
};

export const listSessions = async (): Promise<ChatSession[]> => {
  const response = await fetchApi(`${API_BASE}/sessions`);
  if (!response.ok) throw new Error('会话列表加载失败');
  const data = (await response.json()) as ApiSession[];
  return data.map(toSession);
};

export const createSession = async (): Promise<ChatSession> => {
  const response = await fetchApi(`${API_BASE}/sessions`, { method: 'POST' });
  if (!response.ok) throw new Error('创建会话失败');
  return toSession((await response.json()) as ApiSession);
};

export const renameSession = async (sessionId: string, title: string): Promise<ChatSession> => {
  const response = await fetchApi(`${API_BASE}/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) throw new Error('重命名会话失败');
  return toSession((await response.json()) as ApiSession);
};

export const deleteSession = async (sessionId: string) => {
  const response = await fetchApi(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' });
  if (!response.ok && response.status !== 204) throw new Error('删除会话失败');
};

export const listMessages = async (sessionId: string): Promise<ChatMessage[]> => {
  const response = await fetchApi(`${API_BASE}/sessions/${sessionId}/messages`);
  if (!response.ok) throw new Error('消息加载失败');
  const data = (await response.json()) as ApiMessage[];
  return data.map(toMessage);
};

export const listDocuments = async (): Promise<KnowledgeDocument[]> => {
  const response = await fetchApi(`${API_BASE}/documents`);
  if (!response.ok) throw new Error('文档列表加载失败');
  const data = (await response.json()) as ApiDocument[];
  return data.map(toDocument);
};

export const uploadDocuments = async (files: File[]): Promise<KnowledgeDocument[]> => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const response = await fetchApi(`${API_BASE}/documents`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error('文档上传失败');
  const data = (await response.json()) as ApiDocument[];
  return data.map(toDocument);
};

export const deleteDocument = async (documentId: string) => {
  const response = await fetchApi(`${API_BASE}/documents/${documentId}`, { method: 'DELETE' });
  if (!response.ok && response.status !== 204) throw new Error('文档删除失败');
};

export const streamChat = async (
  payload: StreamRequest,
  handlers: {
    onEvent: (event: StreamEvent) => void;
    signal?: AbortSignal;
  },
) => {
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
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split('\n\n');
    buffer = blocks.pop() ?? '';
    blocks.flatMap(parseSseChunk).forEach(handlers.onEvent);
  }

  if (buffer.trim()) {
    parseSseChunk(buffer).forEach(handlers.onEvent);
  }
};