import { ref } from 'vue';
import { deleteDocument, listDocuments, uploadDocuments } from '../services/chat';
import { readJson, storageKeys, writeJson } from '../utils/storage';
const DEFAULT_SETTINGS = {
    model: 'glm-4-flash',
    temperature: 0.7,
    systemPrompt: '你是一个清晰、直接、可靠的中文 AI 助手。',
    useRag: false,
    documentIds: [],
};
const loadPersistedSettings = () => {
    return readJson(storageKeys.settings, DEFAULT_SETTINGS);
};
const persistSettings = (value) => {
    writeJson(storageKeys.settings, value);
};
export const useSettings = () => {
    const settings = ref(loadPersistedSettings());
    const availableDocuments = ref([]);
    const isUploadingDocuments = ref(false);
    const documentError = ref(null);
    const updateSettings = (next) => {
        settings.value = next;
        persistSettings(next);
    };
    const loadDocuments = async () => {
        documentError.value = null;
        availableDocuments.value = await listDocuments();
    };
    const handleUploadDocuments = async (files) => {
        if (!files.length)
            return;
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
        }
        catch (error) {
            documentError.value = error instanceof Error ? error.message : '文档上传失败';
        }
        finally {
            isUploadingDocuments.value = false;
        }
    };
    const handleDeleteDocument = async (documentId) => {
        documentError.value = null;
        try {
            await deleteDocument(documentId);
            availableDocuments.value = availableDocuments.value.filter((item) => item.id !== documentId);
            settings.value = {
                ...settings.value,
                documentIds: settings.value.documentIds.filter((id) => id !== documentId),
            };
            persistSettings(settings.value);
        }
        catch (error) {
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
