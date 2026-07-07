export type ChatRole = 'user' | 'assistant' | 'system';
export type MessageStatus = 'pending' | 'streaming' | 'done' | 'error' | 'aborted';

export interface KnowledgeSource {
  documentId: string;
  filename: string;
  score: number;
  chunkIndex?: number;
  preview?: string;
}

export interface KnowledgeDocument {
  id: string;
  filename: string;
  contentType: string;
  status: string;
  createdAt: string;
}

export interface SessionSettings {
  model: string;
  temperature: number;
  systemPrompt: string;
  useRag: boolean;
  documentIds: string[];
}

export interface ChatSession {
  id: string;
  title: string;
  model: string;
  systemPrompt: string;
  temperature: number;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  role: ChatRole;
  content: string;
  status: MessageStatus;
  createdAt: string;
  sources?: KnowledgeSource[];
}

export interface StreamEvent {
  type: 'session_created' | 'message_started' | 'token' | 'message_done' | 'error';
  sessionId?: string;
  messageId?: string;
  delta?: string;
  meta?: Record<string, unknown>;
}

export interface StreamRequest {
  sessionId?: string | null;
  message: string;
  settings: SessionSettings;
}