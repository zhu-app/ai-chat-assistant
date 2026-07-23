import { onScopeDispose, ref } from 'vue';
import { deleteDocument, listDocuments, retryDocument, uploadDocuments } from '../services/chat';
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
  let documentPollTimer: ReturnType<typeof setTimeout> | null = null;
  let documentLoadVersion = 0;

  const scheduleDocumentRefresh = () => {
    if (documentPollTimer) clearTimeout(documentPollTimer);
    documentPollTimer = null;
    if (!availableDocuments.value.some((document) => document.status === 'processing' || document.status === 'uploaded')) {
      return;
    }
    documentPollTimer = setTimeout(async () => {
      try {
        await loadDocuments();
      } catch {
        documentError.value = 'Failed to refresh document status';
      }
    }, 1500);
  };

  const updateSettings = (next: SessionSettings) => {
    settings.value = next;
    persistSettings(next);
  };

  const loadDocuments = async () => {
    const version = ++documentLoadVersion;
    documentError.value = null;
    let loaded: KnowledgeDocument[];
    try {
      loaded = await listDocuments();
    } catch (reason) {
      if (version !== documentLoadVersion) return;
      throw reason;
    }
    if (version !== documentLoadVersion) return;
    availableDocuments.value = loaded;
    const availableIds = new Set(loaded.map((document) => document.id));
    const documentIds = settings.value.documentIds.filter((id) => availableIds.has(id));
    if (documentIds.length !== settings.value.documentIds.length) {
      settings.value = { ...settings.value, documentIds };
      persistSettings(settings.value);
    }
    scheduleDocumentRefresh();
  };

  const resetDocuments = () => {
    documentLoadVersion += 1;
    if (documentPollTimer) clearTimeout(documentPollTimer);
    documentPollTimer = null;
    availableDocuments.value = [];
    documentError.value = null;
    isUploadingDocuments.value = false;
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
      scheduleDocumentRefresh();
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

  const handleRetryDocument = async (documentId: string) => {
    documentError.value = null;
    try {
      const updated = await retryDocument(documentId);
      availableDocuments.value = availableDocuments.value.map((item) =>
        item.id === documentId ? updated : item,
      );
      scheduleDocumentRefresh();
    } catch (error) {
      documentError.value = error instanceof Error ? error.message : 'Failed to retry document indexing';
    }
  };

  onScopeDispose(() => {
    if (documentPollTimer) clearTimeout(documentPollTimer);
  });

  return {
    settings,
    availableDocuments,
    isUploadingDocuments,
    documentError,
    updateSettings,
    loadDocuments,
    handleUploadDocuments,
    handleDeleteDocument,
    handleRetryDocument,
    resetDocuments,
  };
};
