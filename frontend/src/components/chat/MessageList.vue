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
}>();

const listRef = ref<HTMLDivElement | null>(null);
const copiedMessageId = ref<string | null>(null);
const showOptimizedPrompt = ref(false);
const showAgentDetails = ref(true);

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
        <div class="message-item__label">{{ message.role === 'user' ? '你' : 'AI' }}</div>

        <div class="message-item__bubble">
          <div
            v-if="message.content"
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

        <div v-if="message.role === 'assistant'" class="message-item__actions">
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
        </div>
      </div>
    </article>

    <div v-if="assistantEntries.length >= 2" class="message-list__hint">
      支持重试最近一轮回答
    </div>
  </div>
</template>