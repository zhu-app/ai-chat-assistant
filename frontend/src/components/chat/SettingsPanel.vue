<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import type { KnowledgeDocument, SessionSettings } from '../../types/chat';
import { readJson, writeJson } from '../../utils/storage';

const props = defineProps<{
  settings: SessionSettings;
  documents: KnowledgeDocument[];
  isUploadingDocuments: boolean;
  documentError: string | null;
}>();

const emit = defineEmits<{
  update: [value: SessionSettings];
  upload: [files: File[]];
  removeDocument: [documentId: string];
  openDocumentManager: [];
}>();

const AVAILABLE_MODELS = [
  { value: 'glm-4-flash', label: 'GLM-4-Flash（免费⚡）' },
  { value: 'glm-4-plus', label: 'GLM-4-Plus（强💪）' },
  { value: 'glm-4-air', label: 'GLM-4-Air（轻量🌤）' },
  { value: 'glm-4-long', label: 'GLM-4-Long（长文本📜）' },
];

const updateField = <K extends keyof SessionSettings>(key: K, value: SessionSettings[K]) => {
  emit('update', { ...props.settings, [key]: value });
};

const toggleDocument = (documentId: string, checked: boolean) => {
  const nextIds = checked
    ? Array.from(new Set([...props.settings.documentIds, documentId]))
    : props.settings.documentIds.filter((id) => id !== documentId);
  emit('update', { ...props.settings, documentIds: nextIds });
};

const handleModelChange = (event: Event) => {
  updateField('model', (event.target as HTMLSelectElement).value);
};

const handleTemperatureInput = (event: Event) => {
  updateField('temperature', Number((event.target as HTMLInputElement).value));
};

const handleSystemPromptInput = (event: Event) => {
  updateField('systemPrompt', (event.target as HTMLTextAreaElement).value);
};

const handleUseRagChange = (event: Event) => {
  updateField('useRag', (event.target as HTMLInputElement).checked);
};

const handleDocumentToggle = (documentId: string, event: Event) => {
  toggleDocument(documentId, (event.target as HTMLInputElement).checked);
};

const handleUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  emit('upload', files);
  input.value = '';
};

// ── 系统提示词预设 ──
const presetName = ref('');
const STORAGE_KEY = 'ai-chat-mvp:prompt-presets';
const savedPresets = ref<Array<{ name: string; prompt: string }>>(readJson(STORAGE_KEY, []));
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

// 从后端加载推荐角色
const defaultRoles = ref<Array<{ name: string; prompt: string; msg: string }>>([]);
onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/templates`);
    if (res.ok) {
      const templates = await res.json();
      defaultRoles.value = templates.map((t: any) => ({
        name: t.title,
        prompt: t.system_prompt || '',
        msg: t.suggested_message || '',
      }));
    }
  } catch { /* ignore */ }
});

const savePreset = () => {
  const name = presetName.value.trim();
  if (!name || !props.settings.systemPrompt.trim()) return;
  savedPresets.value = [...savedPresets.value.filter(p => p.name !== name), { name, prompt: props.settings.systemPrompt }];
  writeJson(STORAGE_KEY, savedPresets.value);
  presetName.value = '';
};

const applyPreset = (prompt: string) => {
  emit('update', { ...props.settings, systemPrompt: prompt });
};

const deletePreset = (name: string) => {
  savedPresets.value = savedPresets.value.filter(p => p.name !== name);
  writeJson(STORAGE_KEY, savedPresets.value);
};
</script>

<template>
  <section class="settings-panel">
    <div class="panel-title">设置</div>

    <!-- ═══ 模型与参数 ═══ -->
    <div class="settings-section">
      <div class="settings-section__title">模型与参数</div>

      <label class="field">
        <span>模型</span>
        <select :value="settings.model" @change="handleModelChange" class="field__select">
          <option v-for="model in AVAILABLE_MODELS" :key="model.value" :value="model.value">
            {{ model.label }}
          </option>
        </select>
      </label>

      <label class="field">
        <span class="field__row-label">
          创造力度
          <small class="field__value-tag">{{ settings.temperature.toFixed(1) }}</small>
        </span>
        <input type="range" min="0" max="1.5" step="0.1" :value="settings.temperature" @input="handleTemperatureInput" />
        <div class="field__range-labels">
          <small>严谨</small>
          <small>自由</small>
        </div>
      </label>
    </div>

    <!-- ═══ AI 角色设定 ═══（核心，放在最前面） -->
    <div class="settings-section">
      <div class="settings-section__title">AI 角色设定</div>

      <label class="field">
        <textarea rows="3" :value="settings.systemPrompt" @input="handleSystemPromptInput"
          placeholder="例如：你是一个专业的编程助手…" class="field__textarea" />
      </label>

      <!-- 预设 -->
      <div class="preset-area">
        <!-- 推荐角色（从后端加载） -->
        <div v-if="defaultRoles.length" class="preset-area__group">
          <div class="preset-area__group-label">推荐角色</div>
          <div class="preset-area__chips">
            <button v-for="role in defaultRoles" :key="role.name"
              class="preset-chip preset-chip--default"
              :class="{ 'preset-chip--active': settings.systemPrompt === role.prompt }"
              @click="applyPreset(role.prompt)">
              {{ role.name }}
            </button>
          </div>
        </div>
        <!-- 用户自定义预设 -->
        <div v-if="savedPresets.length" class="preset-area__group">
          <div class="preset-area__group-label">我的预设</div>
          <div class="preset-area__chips">
            <button v-for="preset in savedPresets" :key="preset.name"
              class="preset-chip"
              :class="{ 'preset-chip--active': settings.systemPrompt === preset.prompt }"
              @click="applyPreset(preset.prompt)">
              {{ preset.name }}
              <span class="preset-chip__del" @click.stop="deletePreset(preset.name)">✕</span>
            </button>
          </div>
        </div>
        <div class="preset-area__save">
          <input class="preset-area__input" v-model="presetName" placeholder="保存当前提示词为预设…" @keydown.enter.prevent="savePreset" />
          <button class="preset-area__btn" @click="savePreset" :disabled="!presetName.trim() || !settings.systemPrompt.trim()">+</button>
        </div>
      </div>
    </div>

    <!-- ═══ 增强功能 ═══ -->
    <div class="settings-section">
      <div class="settings-section__title">增强功能</div>

      <label class="field field--row">
        <span>🌐 联网搜索</span>
        <input type="checkbox" :checked="settings.enableWebSearch" @change="updateField('enableWebSearch', ($event.target as HTMLInputElement).checked)" />
      </label>
      <small class="field-hint" v-if="settings.enableWebSearch">AI 自动搜索互联网获取实时信息</small>

      <label class="field field--row">
        <span>✨ Prompt 优化</span>
        <input type="checkbox" :checked="settings.enablePromptOptimizer" @change="updateField('enablePromptOptimizer', ($event.target as HTMLInputElement).checked)" />
      </label>
      <small class="field-hint" v-if="settings.enablePromptOptimizer">自动将模糊提问改写为结构化问题</small>

      <label class="field field--row">
        <span>🤖 Agent 协作</span>
        <input type="checkbox" :checked="settings.enableAgentMode" @change="updateField('enableAgentMode', ($event.target as HTMLInputElement).checked)" />
      </label>
      <small class="field-hint" v-if="settings.enableAgentMode">多 Agent 协作：分析 → 搜索 → 撰写 → 审查</small>

      <label class="field field--row">
        <span>📚 RAG 知识库</span>
        <input type="checkbox" :checked="settings.useRag" @change="handleUseRagChange" />
      </label>
    </div>

    <!-- ═══ 知识库 ═══ -->
    <div class="settings-section">
      <div class="settings-section__title">知识库文档</div>
      <button class="settings-btn" @click="emit('openDocumentManager')">
        📄 管理文档
        <span v-if="documents.length" class="settings-btn__badge">{{ documents.length }}</span>
      </button>
      <small class="field-hint" v-if="documents.length">
        {{ settings.documentIds.length }} / {{ documents.length }} 个文档已选中
      </small>
    </div>
  </section>
</template>