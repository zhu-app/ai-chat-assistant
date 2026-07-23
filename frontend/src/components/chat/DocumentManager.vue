<script setup lang="ts">
import { ref } from 'vue';
import type { KnowledgeDocument } from '../../types/chat';

const props = defineProps<{
  documents: KnowledgeDocument[];
  selectedIds: string[];
  isUploading: boolean;
  error: string | null;
}>();

const emit = defineEmits<{
  close: [];
  upload: [files: File[]];
  remove: [documentId: string];
  retry: [documentId: string];
  toggle: [documentId: string, checked: boolean];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);

const handleUpload = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (files.length) emit('upload', files);
  input.value = '';
};

const handleDragOver = (e: DragEvent) => { e.preventDefault(); isDragOver.value = true; };
const handleDragLeave = () => { isDragOver.value = false; };
const handleDrop = (e: DragEvent) => {
  e.preventDefault(); isDragOver.value = false;
  const files = Array.from(e.dataTransfer?.files ?? []);
  if (files.length) emit('upload', files);
};
</script>

<template>
  <div class="doc-overlay" @click.self="emit('close')">
    <div class="doc-dialog">
      <div class="doc-dialog__header">
        <span>📚 知识库文档</span>
        <button class="doc-dialog__close" @click="emit('close')">✕</button>
      </div>
      <div class="doc-dialog__body">
        <div class="upload-zone" :class="{ 'upload-zone--drag': isDragOver, 'upload-zone--disabled': isUploading }"
          @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop"
          @click="fileInput?.click()">
          <input ref="fileInput" type="file" accept=".txt,.md,.pdf,.docx" multiple hidden :disabled="isUploading" @change="handleUpload" />
          <template v-if="isUploading"><span class="upload-zone__icon">⏳</span><span>上传中…</span></template>
          <template v-else-if="isDragOver"><span class="upload-zone__icon">📥</span><span>松开上传</span></template>
          <template v-else><span class="upload-zone__icon">📄</span><span>上传文档</span><small class="upload-zone__hint">txt / md / pdf / docx</small></template>
        </div>
        <p v-if="error" class="error-banner">{{ error }}</p>
        <div v-if="documents.length" class="doc-list">
          <label v-for="doc in documents" :key="doc.id" class="doc-item">
            <input type="checkbox" :checked="selectedIds.includes(doc.id)" :disabled="doc.status !== 'ready'"
              @change="emit('toggle', doc.id, ($event.target as HTMLInputElement).checked)" />
            <div class="doc-item__info">
              <strong>{{ doc.filename }}</strong>
              <small>{{ doc.status === 'ready' ? '✅ 就绪' : doc.status === 'processing' ? '⏳ 处理中' : doc.status === 'uploaded' ? '⏱️ 排队中' : '❌ 错误' }}</small>
            </div>
            <button v-if="doc.status === 'error'" class="doc-item__retry" @click.prevent="emit('retry', doc.id)">重试</button>
            <button class="doc-item__del" @click.prevent="emit('remove', doc.id)">删除</button>
          </label>
        </div>
        <div v-else class="doc-empty"><p>还没有上传文档</p><small>上传后选中即可用于 RAG 检索</small></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-overlay { position: fixed; inset: 0; z-index: 100; background: var(--overlay); display: flex; align-items: center; justify-content: center; animation: fadeIn 0.15s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.doc-dialog { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 16px; width: 480px; max-width: 90vw; max-height: 70vh; display: flex; flex-direction: column; box-shadow: var(--shadow-lg); animation: slideUp 0.2s ease; }
@keyframes slideUp { from { transform: translateY(12px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.doc-dialog__header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border-light); font-weight: 600; font-size: 15px; color: var(--text-primary); }
.doc-dialog__close { background: none; border: 0; font-size: 16px; color: var(--text-muted); cursor: pointer; padding: 4px; }
.doc-dialog__close:hover { color: var(--text-primary); }
.doc-dialog__body { padding: 16px 20px; overflow-y: auto; display: grid; gap: 12px; }
.doc-list { display: grid; gap: 6px; max-height: 300px; overflow-y: auto; }
.doc-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border: 1px solid var(--border-light); border-radius: 10px; cursor: pointer; transition: background 0.1s ease; }
.doc-item:hover { background: var(--bg-hover); }
.doc-item__info { flex: 1; min-width: 0; }
.doc-item__info strong { display: block; font-size: 13px; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-item__info small { font-size: 11px; color: var(--text-muted); }
.doc-item__del { padding: 4px 10px; border: 0; border-radius: 6px; font-size: 11px; color: var(--text-muted); background: var(--bg-card); cursor: pointer; transition: all 0.1s ease; flex-shrink: 0; }
.doc-item__retry { padding: 4px 10px; border: 1px solid var(--border); border-radius: 6px; font-size: 11px; color: var(--text-primary); background: var(--bg-secondary); cursor: pointer; flex-shrink: 0; }
.doc-item__del:hover { color: var(--danger); background: var(--danger-soft); }
.doc-empty { text-align: center; padding: 20px; color: var(--text-muted); }
.doc-empty p { margin: 0 0 4px; font-size: 14px; }
.doc-empty small { font-size: 12px; }
</style>
