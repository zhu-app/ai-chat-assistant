<script setup lang="ts">
import { onMounted, ref } from 'vue';
import DOMPurify from 'dompurify';
import { Marked } from 'marked';
import { markedHighlight } from 'marked-highlight';

const props = defineProps<{ token: string }>();
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

let markedInstance: Marked | null = null;

function getMarked(): Marked {
  if (markedInstance) return markedInstance;
  markedInstance = new Marked(
    markedHighlight({
      langPrefix: 'hljs language-',
      highlight(code: string, lang: string) {
        try {
          const hljs = (window as any).__hljs;
          if (hljs && lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
          }
          return code;
        } catch { return code; }
      },
    }),
    { gfm: true, breaks: true },
  );
  return markedInstance;
}

const renderMarkdown = (content: string): string => {
  if (!content) return '';
  try {
    const html = getMarked().parse(content);
    return typeof html === 'string'
      ? DOMPurify.sanitize(html, {
          USE_PROFILES: { html: true },
          FORBID_TAGS: ['style', 'iframe', 'object', 'embed', 'form'],
          FORBID_ATTR: ['style'],
        })
      : escapeHtml(content);
  } catch {
    return escapeHtml(content);
  }
};

const escapeHtml = (text: string) => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

type SharedMessage = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: string;
};

const title = ref('共享对话');
const messages = ref<SharedMessage[]>([]);
const isLoading = ref(true);
const error = ref('');

onMounted(async () => {
  try {
    const response = await fetch(
      `${API_BASE}/sessions/shared/${encodeURIComponent(props.token)}`,
    );
    if (!response.ok) {
      throw new Error(response.status === 404 ? '分享链接无效或已过期' : '加载分享内容失败');
    }
    const data = await response.json();
    title.value = data.session?.title || title.value;
    messages.value = Array.isArray(data.messages) ? data.messages : [];
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '加载分享内容失败';
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <main class="shared-page">
    <header class="shared-header">
      <a class="shared-brand" href="/">AI Chat Assistant</a>
      <span class="shared-badge">只读分享</span>
    </header>

    <section class="shared-content">
      <div class="shared-title">
        <p>公开对话</p>
        <h1>{{ title }}</h1>
      </div>

      <p v-if="isLoading" class="shared-state">正在加载...</p>
      <p v-else-if="error" class="shared-state shared-state--error">{{ error }}</p>
      <div v-else class="shared-messages">
        <article
          v-for="(message, index) in messages"
          :key="`${message.createdAt}-${index}`"
          class="shared-message"
          :class="`shared-message--${message.role}`"
        >
          <div class="shared-message__meta">
            <strong>{{ message.role === 'user' ? '用户' : message.role === 'assistant' ? 'AI' : '系统' }}</strong>
            <time>{{ new Date(message.createdAt).toLocaleString() }}</time>
          </div>
          <div class="shared-message__content" v-html="renderMarkdown(message.content)" />
        </article>
        <p v-if="messages.length === 0" class="shared-state">这段对话还没有消息。</p>
      </div>
    </section>
  </main>
</template>

<style scoped>
.shared-page {
  min-height: 100vh;
  background: var(--bg-primary, #f5f7fa);
  color: var(--text-primary, #17202a);
}

.shared-header {
  height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-color, #d9e0e8);
  background: var(--bg-secondary, #fff);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.shared-brand {
  color: inherit;
  font-size: 16px;
  font-weight: 700;
  text-decoration: none;
}

.shared-badge {
  color: #446078;
  font-size: 13px;
}

.shared-content {
  width: min(820px, calc(100% - 32px));
  margin: 0 auto;
  padding: 48px 0 80px;
}

.shared-title p {
  margin: 0 0 8px;
  color: #547087;
  font-size: 13px;
}

.shared-title h1 {
  margin: 0 0 32px;
  font-size: clamp(26px, 5vw, 38px);
  line-height: 1.25;
}

.shared-messages {
  display: grid;
  gap: 16px;
}

.shared-message {
  padding: 18px 20px;
  border: 1px solid var(--border-color, #d9e0e8);
  border-radius: 8px;
  background: var(--bg-secondary, #fff);
}

.shared-message--user {
  border-left: 4px solid #238b75;
}

.shared-message--assistant {
  border-left: 4px solid #3f6ea8;
}

.shared-message__meta {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: #62778a;
  font-size: 12px;
}

.shared-message p {
  margin: 0;
  line-height: 1.75;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.shared-state {
  padding: 40px 0;
  color: #62778a;
  text-align: center;
}

.shared-state--error {
  color: #b42318;
}

@media (max-width: 600px) {
  .shared-header {
    padding: 0 16px;
  }

  .shared-content {
    padding-top: 32px;
  }

  .shared-message__meta {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }
}
</style>
