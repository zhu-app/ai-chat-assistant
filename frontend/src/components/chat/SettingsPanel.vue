<script setup lang="ts">
import { computed, ref } from 'vue';
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
}>();

const AVAILABLE_MODELS = [
  { value: 'glm-4-flash', label: 'GLM-4-Flash（免费⚡）' },
  { value: 'glm-4-plus', label: 'GLM-4-Plus（强💪）' },
  { value: 'glm-4-air', label: 'GLM-4-Air（轻量🌤）' },
  { value: 'glm-4-long', label: 'GLM-4-Long（长文本📜）' },
];

const isDragOver = ref(false);

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

const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = true;
};

const handleDragLeave = () => {
  isDragOver.value = false;
};

const handleDrop = (e: DragEvent) => {
  e.preventDefault();
  isDragOver.value = false;
  const files = Array.from(e.dataTransfer?.files ?? []);
  if (files.length) emit('upload', files);
};

// ── 系统提示词预设 ──
const presetName = ref('');
const STORAGE_KEY = 'ai-chat-mvp:prompt-presets';
const savedPresets = ref<Array<{ name: string; prompt: string }>>(readJson(STORAGE_KEY, []));

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
        <div class="preset-area__chips" v-if="savedPresets.length">
          <button v-for="preset in savedPresets" :key="preset.name"
            class="preset-chip" :class="{ 'preset-chip--active': settings.systemPrompt === preset.prompt }"
            @click="applyPreset(preset.prompt)">
            {{ preset.name }}
            <span class="preset-chip__del" @click.stop="deletePreset(preset.name)">✕</span>
          </button>
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

      <div class="upload-zone" :class="{ 'upload-zone--drag': isDragOver, 'upload-zone--disabled': isUploadingDocuments }"
        @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop"
        @click="($refs.fileInput as HTMLInputElement)?.click()">
        <input ref="fileInput" type="file" accept=".txt,.md,.pdf,.docx" multiple hidden :disabled="isUploadingDocuments" @change="handleUpload" />
        <template v-if="isUploadingDocuments">
          <span class="upload-zone__icon">⏳</span>
          <span>上传中…</span>
        </template>
        <template v-else-if="isDragOver">
          <span class="upload-zone__icon">📥</span>
          <span>松开上传</span>
        </template>
        <template v-else>
          <span class="upload-zone__icon">📄</span>
          <span>上传文档</span>
          <small class="upload-zone__hint">txt / md / pdf / docx</small>
        </template>
      </div>

      <p v-if="documentError" class="error-banner settings-error">{{ documentError }}</p>

      <div v-if="documents.length" class="document-list">
        <label v-for="document in documents" :key="document.id" class="document-item">
          <div class="document-item__main">
            <input type="checkbox" :checked="settings.documentIds.includes(document.id)" @change="handleDocumentToggle(document.id, $event)" />
            <div>
              <strong>{{ document.filename }}</strong>
              <small>{{ document.status }}</small>
            </div>
          </div>
          <button type="button" class="document-item__remove" @click="emit('removeDocument', document.id)">删除</button>
        </label>
      </div>
      <div v-else class="empty-panel"><small>还没有上传文档</small></div>
    </div>
  </section>
</template>