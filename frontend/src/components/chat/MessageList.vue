<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { Marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import type { ChatMessage } from '../../types/chat';

// 同步创建 marked 实例（marked 本身很小，~50KB）
// highlight.js 按需加载，首次遇到代码块时才异步注入
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
          // highlight.js 还没加载好，先返回原样
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
}>();

const emit = defineEmits<{
  retry: [messageId: string];
}>();

const listRef = ref<HTMLDivElement | null>(null);
const copiedMessageId = ref<string | null>(null);

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

// 同步渲染 Markdown
const renderMessageContent = (content: string): string => {
  if (!content) return '';
  try {
    const html = getMarked().parse(content);
    return typeof html === 'string' ? html : escapeHtml(content);
  } catch {
    return escapeHtml(content);
  }
};

// 消息更新后滚动到底部
watch(
  () => props.messages.map((m) => `${m.id}:${m.content.length}:${m.status}`).join('|'),
  () => {
    scrollToBottom();
  },
  { immediate: true },
);

// 简单的 HTML 转义
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

</script>

<template>
  <div ref="listRef" class="message-list">
    <article
      v-for="(message, index) in messages"
      :key="message.id"
      class="message-item"
      :class="`message-item--${message.role}`"
    >
      <!-- 头像 -->
      <div class="message-item__avatar">
        {{ message.role === 'user' ? '我' : 'AI' }}
      </div>

      <!-- 消息体（标签 + 气泡 + 操作） -->
      <div class="message-item__body">
        <div class="message-item__label">{{ message.role === 'user' ? '你' : 'AI' }}</div>

        <div class="message-item__bubble">
          <div
            v-if="message.content"
            class="message-item__content"
            v-html="renderMessageContent(message.content)"
          />
          <p v-else-if="message.status === 'streaming'">正在生成…</p>
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
      支持重试最近一轮回答，也可以在右侧切换当前检索文档范围。
    </div>
  </div>
</template>