<script setup lang="ts">
import { ref, onMounted } from 'vue';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

interface PromptTemplate {
  id: string;
  emoji: string;
  title: string;
  description: string;
}

const props = defineProps<{
  value: string;
  isStreaming: boolean;
  systemPrompt: string;
}>();

const emit = defineEmits<{
  update: [value: string];
  send: [];
  stop: [];
  applyTemplate: [systemPrompt: string, suggestedMessage: string];
}>();

const showTemplates = ref(false);
const templates = ref<PromptTemplate[]>([]);
const loadingTemplates = ref(false);

onMounted(async () => {
  try {
    loadingTemplates.value = true;
    const res = await fetch(`${API_BASE}/templates`);
    if (res.ok) {
      templates.value = await res.json();
    }
  } catch { /* ignore */ }
  loadingTemplates.value = false;
});

const handleInput = (event: Event) => {
  emit('update', (event.target as HTMLTextAreaElement).value);
};

const onSubmit = () => {
  if (props.isStreaming) {
    emit('stop');
    return;
  }
  emit('send');
};

const selectTemplate = async (templateId: string) => {
  try {
    const res = await fetch(`${API_BASE}/templates/${templateId}`);
    if (res.ok) {
      const detail = await res.json();
      emit('applyTemplate', detail.systemPrompt, detail.suggestedMessage);
      showTemplates.value = false;
    }
  } catch { /* ignore */ }
};
</script>

<template>
  <section class="composer">
    <!-- 模板选择面板 -->
    <div v-if="showTemplates" class="template-panel">
      <div class="template-panel__header">
        <span>📋 场景模板</span>
        <button class="template-panel__close" @click="showTemplates = false">✕</button>
      </div>
      <div class="template-panel__list">
        <button
          v-for="t in templates"
          :key="t.id"
          class="template-card"
          @click="selectTemplate(t.id)"
        >
          <span class="template-card__emoji">{{ t.emoji }}</span>
          <div class="template-card__info">
            <strong>{{ t.title }}</strong>
            <small>{{ t.description }}</small>
          </div>
        </button>
      </div>
    </div>

    <textarea
      class="composer__input"
      :value="value"
      rows="4"
      placeholder="发一条消息，开始新的多轮对话。"
      @input="handleInput"
      @keydown.enter.exact.prevent="onSubmit"
      @keydown.escape.prevent="isStreaming && emit('stop')"
    />

    <div class="composer__actions">
      <div class="composer__actions-left">
        <button
          class="composer__template-btn"
          title="场景模板"
          @click="showTemplates = !showTemplates"
          :disabled="isStreaming"
        >
          📋
        </button>
        <small>Enter 发送 · Shift+Enter 换行 · Esc 停止</small>
      </div>
      <button
        class="primary-button"
        :class="{ 'primary-button--stop': isStreaming }"
        @click="onSubmit"
      >
        {{ isStreaming ? '■ 停止生成' : '发送消息' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.composer__actions-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.composer__template-btn {
  background: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.12s ease;
  line-height: 1;
}

.composer__template-btn:hover {
  background: var(--bg-hover);
  border-color: var(--accent);
}

.composer__template-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.template-panel {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 8px;
  overflow: hidden;
  animation: slideUp 0.2s ease;
}

@keyframes slideUp {
  from { transform: translateY(8px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.template-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-light);
}

.template-panel__header span {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.template-panel__close {
  background: none;
  border: 0;
  font-size: 14px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 4px;
}

.template-panel__close:hover {
  color: var(--text-primary);
}

.template-panel__list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 10px;
  max-height: 260px;
  overflow-y: auto;
}

.template-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--border-light);
  border-radius: 10px;
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.12s ease;
  text-align: left;
  width: 100%;
}

.template-card:hover {
  background: var(--accent-soft);
  border-color: var(--accent);
}

.template-card__emoji {
  font-size: 20px;
  flex-shrink: 0;
}

.template-card__info {
  min-width: 0;
}

.template-card__info strong {
  display: block;
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
}

.template-card__info small {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
  line-height: 1.3;
}
</style>