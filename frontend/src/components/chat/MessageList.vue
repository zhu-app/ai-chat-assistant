<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { Marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import type { AgentPlanMeta, AgentStep, AgentReviewInfo, ChatMessage, PromptOptimizeInfo } from '../../types/chat';

let markedInstance: Marked | null = null;
let hljsLoading = false;
let hljsLoaded = false;

function getMarked(): Marked {
  if (markedInstance) return markedInstance;
  markedInstance = new Marked(
    markedHighlight({
      langPrefix: 'hljs language-',
      highlight(code: string, lang: string) {
        if (!hljsLoaded) {
          if (!hljsLoading) {
            hljsLoading = true;
            import('highlight.js').then((mod) => {
              hljsLoaded = true;
              window.__hljs = mod.default;
            });
          }
          return code;
        }
        const hljs = window.__hljs;
        if (lang && hljs.getLanguage(lang)) {
          try { return hljs.highlight(code, { language: lang }).value; } catch { /* fallthrough */ }
        }
        return hljs.highlightAuto(code).value;
      },
    }),
    { gfm: true, breaks: true },
  );
  return markedInstance;
}

declare global {
  interface Window { __hljs: any; }
}

const props = defineProps<{
  messages: ChatMessage[];
  agentPlan: AgentPlanMeta | null;
  agentSteps: AgentStep[];
  agentReview: AgentReviewInfo | null;
  promptOptimize: PromptOptimizeInfo | null;
  isStreaming: boolean;
  enablePromptOptimizer: boolean;
}>();

const emit = defineEmits<{
  retry: [messageId: string];
  share: [];
}>();

const emitShare = () => {
  emit('share');
};

const listRef = ref<HTMLDivElement | null>(null);
const copiedMessageId = ref<string | null>(null);
const showOptimizedPrompt = ref(false);
const showAgentDetails = ref(true);
const expandedAgentMsg = ref<string | null>(null);

const toggleAgentDetail = (msgId: string) => {
  expandedAgentMsg.value = expandedAgentMsg.value === msgId ? null : msgId;
};

// ── 消息编辑 ──
const editingMessageId = ref<string | null>(null);
const editMessageContent = ref('');
const editTextarea = ref<HTMLTextAreaElement | null>(null);
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

const startEdit = (message: ChatMessage) => {
  editingMessageId.value = message.id;
  editMessageContent.value = message.content;
  nextTick(() => editTextarea.value?.focus());
};

const saveEdit = async (messageId: string) => {
  const content = editMessageContent.value.trim();
  if (!content) return;
  try {
    const msg = props.messages.find(m => m.id === messageId);
    if (!msg) return;
    const res = await fetch(`${API_BASE}/sessions/${msg.sessionId}/messages/${messageId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ content }),
    });
    if (res.ok) {
      msg.content = content;
    }
  } catch { /* ignore */ }
  editingMessageId.value = null;
};

const cancelEdit = () => {
  editingMessageId.value = null;
};

// 判断消息是否为最后一条用户消息（用于内联显示 Prompt 优化结果）
// 注意：不能用 index === messages.length-1，因为 assistant 消息在后面追加
const isLastUserMessage = (index: number) => {
  const msg = props.messages[index];
  if (!msg || msg.role !== 'user') return false;
  for (let i = props.messages.length - 1; i >= 0; i--) {
    if (props.messages[i]?.role === 'user') return i === index;
  }
  return false;
};

const assistantEntries = computed(() => props.messages.filter((message) => message.role === 'assistant'));

onMounted(() => {
  if (props.messages.length > 0) scrollToBottom();
});

const scrollToBottom = async () => {
  await nextTick();
  const container = listRef.value?.closest('.chat-stage') as HTMLElement | null;
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
};

const renderMessageContent = (content: string): string => {
  if (!content) return '';
  try {
    const html = getMarked().parse(content);
    return typeof html === 'string' ? html : escapeHtml(content);
  } catch {
    return escapeHtml(content);
  }
};

watch(
  () => props.messages.map((m) => `${m.id}:${m.content.length}:${m.status}`).join('|'),
  () => {
    scrollToBottom();
  },
  { immediate: true },
);

const escapeHtml = (text: string) => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

const copyMessage = async (message: ChatMessage) => {
  if (!message.content) return;
  await navigator.clipboard.writeText(message.content);
  copiedMessageId.value = message.id;
  window.setTimeout(() => {
    if (copiedMessageId.value === message.id) copiedMessageId.value = null;
  }, 1200);
};

const canRetry = (messageIndex: number) => {
  for (let index = messageIndex - 1; index >= 0; index -= 1) {
    if (props.messages[index]?.role === 'user') return true;
  }
  return false;
};

// 格式化时间
const formatTime = (iso: string) => {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin} 分钟前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} 小时前`;
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

// Agent 步骤状态图标
const stepIcon = (status: string) => {
  if (status === 'running') return '⏳';
  if (status === 'done') return '✅';
  if (status === 'error') return '❌';
  return '⏸';
};

</script>

<template>
  <div ref="listRef" class="message-list">

    <!-- ═══ Agent 工作流进度 ═══ -->
    <div v-if="agentSteps.length" class="agent-workflow">
      <div class="agent-workflow__header" @click="showAgentDetails = !showAgentDetails">
        <span>🤖 Agent 协作中</span>
        <small>{{ showAgentDetails ? '隐藏详情' : '查看详情' }}</small>
      </div>
      <div v-if="showAgentDetails" class="agent-workflow__body">
        <div
          v-for="(step, index) in agentSteps"
          :key="step.agent"
          class="agent-step"
          :class="`agent-step--${step.status}`"
        >
          <div class="agent-step__indicator">{{ stepIcon(step.status) }}</div>
          <div class="agent-step__content">
            <div class="agent-step__title">
              <strong>{{ step.label }}</strong>
              <span class="agent-step__task">{{ step.task }}</span>
            </div>
            <div v-if="step.summary" class="agent-step__summary">{{ step.summary }}</div>
          </div>
          <div v-if="step.status === 'running'" class="agent-step__spinner" />
        </div>
      </div>
    </div>

    <!-- ═══ Agent 审查结果 ═══ -->
    <div v-if="agentReview" class="agent-banner agent-banner--review">
      <div class="agent-banner__header">
        <span>⭐ 质量审查</span>
      </div>
      <div class="agent-banner__body" v-html="renderMessageContent(agentReview.review)" />
    </div>

    <!-- ═══ 消息列表 ═══ -->
    <article
      v-for="(message, index) in messages"
      :key="message.id"
      class="message-item"
      :class="`message-item--${message.role}`"
    >
      <div class="message-item__avatar">
        {{ message.role === 'user' ? '我' : 'AI' }}
      </div>

      <div class="message-item__body">
        <div class="message-item__label">
          {{ message.role === 'user' ? '你' : 'AI' }}
        </div>

        <div class="message-item__bubble">
          <!-- 编辑模式（用户消息） -->
          <div v-if="editingMessageId === message.id" class="message-edit">
            <textarea
              class="message-edit__input"
              v-model="editMessageContent"
              rows="3"
              @keydown.enter.exact.prevent="saveEdit(message.id)"
              @keydown.escape.prevent="cancelEdit"
              ref="editTextarea"
            />
            <div class="message-edit__actions">
              <button class="message-edit__btn message-edit__btn--save" @click="saveEdit(message.id)">保存</button>
              <button class="message-edit__btn" @click="cancelEdit">取消</button>
            </div>
          </div>
          <!-- 显示模式 -->
          <div
            v-else-if="message.content"
            class="message-item__content"
            v-html="renderMessageContent(message.content)"
          />
          <p v-else-if="message.status === 'streaming' && !agentSteps.length" class="message-item__generating">⏳ 思考中</p>
          <p v-else-if="message.status === 'streaming' && agentSteps.length" class="message-item__generating message-item__generating--agent">
            ⏳ Agent 协作中<span class="dot-pulse"><span>.</span><span>.</span><span>.</span></span>
          </p>
          <p v-else-if="message.status === 'aborted'" class="message-item__aborted">已中断</p>

          <div v-if="message.sources?.length" class="message-item__sources">
            <div class="message-item__sources-title">本次回答参考了这些文档</div>
            <div class="message-item__source-list">
              <div v-for="source in message.sources" :key="`${message.id}-${source.documentId}-${source.chunkIndex ?? 0}`" class="message-source-card">
                <div class="message-source-card__main">
                  <strong>{{ source.filename }}</strong>
                  <span>片段 {{ (source.chunkIndex ?? 0) + 1 }} · 相关度 {{ Number(source.score ?? 0).toFixed(0) }}</span>
                  <p v-if="source.preview" class="message-source-card__preview">{{ source.preview }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- ═══ Prompt 优化结果（内联在用户消息下方） ═══ -->
          <div v-if="message.role === 'user' && isLastUserMessage(index) && enablePromptOptimizer">
            <!-- 优化中提示：流式进行中 + 还没有优化结果返回 → 正在优化 -->
            <div v-if="isStreaming && !promptOptimize" class="opt-inline opt-inline--pending">
              <span class="opt-inline__icon">✨</span>
              <span>正在优化提问</span>
              <span class="opt-inline__spinner" />
            </div>
            <!-- 优化完成 -->
            <div v-else-if="promptOptimize && !promptOptimize.skipped" class="opt-inline">
              <div class="opt-inline__header" @click="showOptimizedPrompt = !showOptimizedPrompt">
                <span class="opt-inline__icon">✨</span>
                <span>提问已优化</span>
                <small class="opt-inline__toggle">{{ showOptimizedPrompt ? '收起' : '查看详情' }}</small>
              </div>
              <div v-if="showOptimizedPrompt" class="opt-inline__body">
                <div class="opt-compare">
                  <div class="opt-compare__item">
                    <small class="opt-compare__label">原始</small>
                    <p class="opt-compare__text">{{ promptOptimize.original }}</p>
                  </div>
                  <div class="opt-compare__arrow">→</div>
                  <div class="opt-compare__item">
                    <small class="opt-compare__label">优化后</small>
                    <p class="opt-compare__text opt-compare__text--optimized">{{ promptOptimize.optimized }}</p>
                  </div>
                </div>
                <div v-if="promptOptimize.strategies.length" class="opt-strategies">
                  <small>策略：{{ promptOptimize.strategies.join('、') }}</small>
                </div>
                <small class="opt-reason">{{ promptOptimize.reason }}</small>
              </div>
            </div>
          </div>
        </div>

        <!-- 用户消息操作：编辑 -->
        <div v-if="message.role === 'user' && message.status === 'done'" class="message-item__actions">
          <span class="message-item__time">{{ formatTime(message.createdAt) }}</span>
          <div class="message-item__actions-right">
            <button type="button" class="message-action" @click="startEdit(message)">
              编辑
            </button>
          </div>
        </div>

        <div v-if="message.role === 'assistant'" class="message-item__actions">
          <span class="message-item__time">{{ formatTime(message.createdAt) }}</span>
          <div class="message-item__actions-right">
            <!-- Agent 徽章（签名元素） -->
            <button
              v-if="message.agentInfo?.steps?.length"
              class="agent-badge"
              :class="{ 'agent-badge--expanded': expandedAgentMsg === message.id }"
              @click="toggleAgentDetail(message.id)"
              :title="'查看 Agent 协作详情'"
            >
              🤖 <span class="agent-badge__count">{{ message.agentInfo.steps.length }}</span>
            </button>
            <button type="button" class="message-action" @click="copyMessage(message)">
              {{ copiedMessageId === message.id ? '已复制' : '复制' }}
            </button>
            <button
              v-if="canRetry(index)"
              type="button"
              class="message-action"
              @click="emit('retry', message.id)"
            >
              重试
            </button>
            <button type="button" class="message-action message-action--share" @click="emitShare()">
              分享
            </button>
          </div>
        </div>
        <!-- Agent 协作详情（展开后显示） -->
        <div v-if="message.agentInfo?.steps?.length && expandedAgentMsg === message.id" class="agent-detail">
          <div class="agent-detail__header">🤖 Agent 协作</div>
          <div
            v-for="step in message.agentInfo.steps"
            :key="step.agent"
            class="agent-detail__step"
          >
            <span class="agent-detail__icon">{{ step.status === 'done' ? '✅' : step.status === 'error' ? '❌' : '⏳' }}</span>
            <span class="agent-detail__label">{{ step.label }}</span>
            <span class="agent-detail__task">{{ step.task }}</span>
          </div>
          <div v-if="message.agentInfo.review" class="agent-detail__review" v-html="renderMessageContent(message.agentInfo.review)" />
        </div>
      </div>
    </article>

    <div v-if="assistantEntries.length >= 2" class="message-list__hint">
      支持重试最近一轮回答
    </div>
  </div>
</template>