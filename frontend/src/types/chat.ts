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
  enablePromptOptimizer: boolean;
  enableAgentMode: boolean;
  enableWebSearch: boolean;
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
  agentInfo?: {
    steps: AgentStep[];
    review?: string;
  };
}

export interface AgentStepMeta {
  agent: string;
  label: string;
  task: string;
  summary?: string;
}

export interface AgentPlanMeta {
  steps: Array<{ agent: string; task: string }>;
  reason: string;
}

export interface StreamEvent {
  type: 'session_created' | 'message_started' | 'token' | 'message_done' | 'error'
    | 'prompt_optimized' | 'agent_plan' | 'agent_step_start' | 'agent_step_done'
    | 'agent_review' | 'agent_synthesized' | 'telemetry';
  sessionId?: string;
  messageId?: string;
  delta?: string;
  meta?: Record<string, unknown>;
}

export interface TelemetryData {
  firstTokenLatencyMs?: number;
  totalDurationMs?: number;
  tokensPerSecond?: number;
  inputTokens?: number;
  outputTokens?: number;
  estimatedCostUsd?: number;
  ragChunksRetrieved?: number;
  ragTopScore?: number;
  qualityScore?: number;
  qualityDetails?: {
    accuracy: number;
    completeness: number;
    clarity: number;
    usefulness: number;
    summary: string;
  };
}

export interface StreamRequest {
  sessionId?: string | null;
  message: string;
  settings: SessionSettings;
}

// ── Agent 工作流类型 ──

export interface AgentStep {
  agent: string;
  label: string;
  task: string;
  status: 'pending' | 'running' | 'done' | 'error';
  summary?: string;
}

export interface AgentReviewInfo {
  review: string;
}

export interface PromptOptimizeInfo {
  original: string;
  optimized: string;
  strategies: string[];
  reason: string;
  skipped?: boolean;
}