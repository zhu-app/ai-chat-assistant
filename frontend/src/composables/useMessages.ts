import { computed, ref } from 'vue';
import { listMessages, streamChat } from '../services/chat';
import type { AgentPlanMeta, AgentReviewInfo, AgentStep, ChatMessage, PromptOptimizeInfo, SessionSettings, StreamEvent, TelemetryData } from '../types/chat';
import { uid } from '../utils/id';

/** Agent 工作流中的一个步骤 */

/** Prompt 优化结果 */

/** Agent 审查结果 */

export const useMessages = () => {
  const messages = ref<ChatMessage[]>([]);
  const isStreaming = ref(false);
  const error = ref<string | null>(null);
  const controller = ref<AbortController | null>(null);

  // Agent 模式状态
  const agentPlan = ref<AgentPlanMeta | null>(null);
  const agentSteps = ref<AgentStep[]>([]);
  const agentReview = ref<AgentReviewInfo | null>(null);

  // Prompt 优化状态
  const promptOptimize = ref<PromptOptimizeInfo | null>(null);

  // 遥测数据
  const telemetry = ref<TelemetryData | null>(null);
  // Token 用量历史累积（跨消息汇总）
  const telemetryHistory = ref<TelemetryData[]>([]);
  const tokenStats = computed(() => {
    const all = telemetryHistory.value;
    return {
      totalInputTokens: all.reduce((s, t) => s + (t.inputTokens || 0), 0),
      totalOutputTokens: all.reduce((s, t) => s + (t.outputTokens || 0), 0),
      totalCostUsd: all.reduce((s, t) => s + (t.estimatedCostUsd || 0), 0),
      totalDurationMs: all.reduce((s, t) => s + (t.totalDurationMs || 0), 0),
      totalMessages: all.length,
      avgQuality: all.length > 0 ? all.reduce((s, t) => s + (t.qualityScore || 0), 0) / all.length : 0,
      avgTokensPerSecond: all.length > 0 ? all.reduce((s, t) => s + (t.tokensPerSecond || 0), 0) / all.length : 0,
    };
  });

  const hasMessages = computed(() => messages.value.length > 0);

  const loadMessages = async (sessionId: string | null) => {
    if (!sessionId) {
      messages.value = [];
      return;
    }
    messages.value = await listMessages(sessionId);
  };

  const stopStream = () => {
    controller.value?.abort();
    controller.value = null;
    isStreaming.value = false;
    const streamingMsg = messages.value.find(
      (item) => item.role === 'assistant' && item.status === 'streaming',
    );
    if (streamingMsg) {
      streamingMsg.status = 'aborted';
      messages.value = [...messages.value];
    }
  };

  const ensureAssistantMessage = (sessionId: string, messageId: string) => {
    const existing = messages.value.find((item) => item.id === messageId);
    if (existing) return existing;

    const created: ChatMessage = {
      id: messageId || uid(),
      sessionId,
      role: 'assistant',
      content: '',
      status: 'streaming',
      createdAt: new Date().toISOString(),
    };
    messages.value = [...messages.value, created];
    return created;
  };

  const applyEvent = (
    event: StreamEvent,
    onSessionCreated: (sessionId: string, title?: string) => void,
  ) => {
    if (event.type === 'session_created' && event.sessionId) {
      onSessionCreated(event.sessionId, String(event.meta?.title ?? '新对话'));
      return;
    }

    if (event.type === 'message_started' && event.sessionId) {
      const messageId = event.messageId || uid();
      ensureAssistantMessage(event.sessionId, messageId);
      return;
    }

    if (event.type === 'token') {
      // Agent 模式下可能没有 messageId，用 find 兜底
      const target = event.messageId
        ? messages.value.find((item) => item.id === event.messageId)
        : messages.value.find((item) => item.role === 'assistant' && item.status === 'streaming');

      if (target) {
        target.content += event.delta ?? '';
        target.status = 'streaming';
        messages.value = [...messages.value];
      } else if (event.sessionId) {
        // 还没有 assistant 消息，创建一个
        const created = ensureAssistantMessage(event.sessionId, event.messageId || uid());
        created.content = event.delta ?? '';
        messages.value = [...messages.value];
      }
      return;
    }

    if (event.type === 'message_done' && event.messageId) {
      const target = messages.value.find((item) => item.id === event.messageId);
      if (target) {
        if (target.status === 'aborted') {
          messages.value = [...messages.value];
          isStreaming.value = false;
          controller.value = null;
          return;
        }
        target.status = 'done';
        if (typeof event.meta?.content === 'string') {
          target.content = event.meta.content;
        }
        if (Array.isArray(event.meta?.sources)) {
          target.sources = event.meta.sources as ChatMessage['sources'];
        }
        messages.value = [...messages.value];
      }
      isStreaming.value = false;
      controller.value = null;

      // 从 message_done 中提取遥测数据
      if (event.meta?.telemetry) {
        const td = event.meta.telemetry as TelemetryData;
        telemetry.value = td;
        telemetryHistory.value = [...telemetryHistory.value, td];
      }
      return;
    }

    if (event.type === 'error') {
      error.value = String(event.meta?.message ?? '生成失败');
      isStreaming.value = false;
      controller.value = null;
      return;
    }

    // ── Prompt 优化事件 ──
    if (event.type === 'prompt_optimized' && event.meta) {
      promptOptimize.value = {
        original: String(event.meta.original ?? ''),
        optimized: String(event.meta.optimized ?? ''),
        strategies: Array.isArray(event.meta.strategies) ? event.meta.strategies as string[] : [],
        reason: String(event.meta.reason ?? ''),
      };
      return;
    }

    // ── Agent 事件 ──
    if (event.type === 'agent_plan' && event.meta) {
      agentPlan.value = event.meta as unknown as AgentPlanMeta;
      // 初始化步骤状态
      const steps = (event.meta.steps as Array<{ agent: string; task: string }>) ?? [];
      agentSteps.value = steps.map((s) => ({
        agent: s.agent,
        label: s.agent,
        task: s.task,
        status: 'pending' as const,
      }));
      return;
    }

    if (event.type === 'agent_step_start' && event.meta) {
      const meta = event.meta as Record<string, unknown>;
      const agentName = String(meta.agent ?? '');
      const step = agentSteps.value.find((s) => s.agent === agentName);
      if (step) {
        step.status = 'running';
        step.label = String(meta.label ?? agentName);
        step.task = String(meta.task ?? step.task);
      }
      agentSteps.value = [...agentSteps.value];
      return;
    }

    if (event.type === 'agent_step_done' && event.meta) {
      const meta = event.meta as Record<string, unknown>;
      const agentName = String(meta.agent ?? '');
      const step = agentSteps.value.find((s) => s.agent === agentName);
      if (step) {
        step.status = 'done';
        step.summary = String(meta.summary ?? '');
      }
      agentSteps.value = [...agentSteps.value];
      return;
    }

    if (event.type === 'agent_review' && event.meta) {
      agentReview.value = {
        review: String((event.meta as Record<string, unknown>).review ?? ''),
      };
      return;
    }

    // ── 遥测事件 ──
    if (event.type === 'telemetry' && event.meta) {
      const phase = (event.meta as Record<string, unknown>).phase as string;
      if (phase === 'done') {
        telemetry.value = event.meta as unknown as TelemetryData;
      }
      return;
    }
  };

  const sendMessage = async (
    payload: {
      sessionId: string | null;
      message: string;
      settings: SessionSettings;
    },
    onSessionCreated: (sessionId: string, title?: string) => void,
  ) => {
    // 重置 Agent / Prompt 状态
    agentPlan.value = null;
    agentSteps.value = [];
    agentReview.value = null;
    promptOptimize.value = null;

    error.value = null;
    isStreaming.value = true;
    controller.value = new AbortController();

    const provisionalSessionId = payload.sessionId ?? 'pending-session';
    messages.value = [
      ...messages.value,
      {
        id: uid(),
        sessionId: provisionalSessionId,
        role: 'user',
        content: payload.message,
        status: 'done',
        createdAt: new Date().toISOString(),
      },
    ];

    try {
      await streamChat(payload, {
        signal: controller.value.signal,
        onEvent: (event) => applyEvent(event, onSessionCreated),
      });
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        isStreaming.value = false;
        controller.value = null;
        return;
      }
      error.value = err instanceof Error ? err.message : '请求失败';
      isStreaming.value = false;
      controller.value = null;
    }
  };

  const clearAgentState = () => {
    agentPlan.value = null;
    agentSteps.value = [];
    agentReview.value = null;
    promptOptimize.value = null;
    telemetry.value = null;
  };

  const clearTokenStats = () => {
    telemetryHistory.value = [];
    telemetry.value = null;
  };

  return {
    messages,
    hasMessages,
    isStreaming,
    error,
    loadMessages,
    sendMessage,
    stopStream,
    // Agent / Prompt 状态
    agentPlan,
    agentSteps,
    agentReview,
    promptOptimize,
    // 遥测数据
    telemetry,
    telemetryHistory,
    tokenStats,
    clearAgentState,
    clearTokenStats,
  };
};