import { ref } from 'vue';
import { deleteDocument, listDocuments, uploadDocuments } from '../services/chat';
import type { KnowledgeDocument, SessionSettings } from '../types/chat';
import { readJson, storageKeys, writeJson } from '../utils/storage';

const DEFAULT_SETTINGS: SessionSettings = {
  model: 'glm-4-flash',
  temperature: 0.7,
  systemPrompt: '你是一个清晰、直接、可靠的中文 AI 助手。',
  useRag: false,
  documentIds: [],
  enablePromptOptimizer: false,
  enableAgentMode: false,
  enableWebSearch: false,
};

const loadPersistedSettings = (): SessionSettings => {
  return readJson<SessionSettings>(storageKeys.settings, DEFAULT_SETTINGS);
};

const persistSettings = (value: SessionSettings) => {
  writeJson(storageKeys.settings, value);
};

export const useSettings = () => {
  const settings = ref<SessionSettings>(loadPersistedSettings());
  const availableDocuments = ref<KnowledgeDocument[]>([]);
  const isUploadingDocuments = ref(false);
  const documentError = ref<string | null>(null);

  const updateSettings = (next: SessionSettings) => {
    settings.value = next;
    persistSettings(next);
  };

  const loadDocuments = async () => {
    documentError.value = null;
    availableDocuments.value = await listDocuments();
  };

  const handleUploadDocuments = async (files: File[]) => {
    if (!files.length) return;
    documentError.value = null;
    isUploadingDocuments.value = true;
    try {
      const uploaded = await uploadDocuments(files);
      availableDocuments.value = [...uploaded, ...availableDocuments.value];
      const mergedIds = Array.from(new Set([...settings.value.documentIds, ...uploaded.map((item) => item.id)]));
      settings.value = {
        ...settings.value,
        useRag: true,
        documentIds: mergedIds,
      };
      persistSettings(settings.value);
    } catch (error) {
      documentError.value = error instanceof Error ? error.message : '文档上传失败';
    } finally {
      isUploadingDocuments.value = false;
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    documentError.value = null;
    try {
      await deleteDocument(documentId);
      availableDocuments.value = availableDocuments.value.filter((item) => item.id !== documentId);
      settings.value = {
        ...settings.value,
        documentIds: settings.value.documentIds.filter((id) => id !== documentId),
      };
      persistSettings(settings.value);
    } catch (error) {
      documentError.value = error instanceof Error ? error.message : '文档删除失败';
    }
  };

  return {
    settings,
    availableDocuments,
    isUploadingDocuments,
    documentError,
    updateSettings,
    loadDocuments,
    handleUploadDocuments,
    handleDeleteDocument,
  };
};