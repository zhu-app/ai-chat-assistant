import { ref, watch } from 'vue';
import { storageKeys } from '../utils/storage';

export const useComposer = (sessionId: () => string | null) => {
  const draft = ref('');

  const syncDraft = (nextSessionId: string | null) => {
    if (!nextSessionId) {
      draft.value = '';
      return;
    }
    draft.value = localStorage.getItem(storageKeys.draft(nextSessionId)) ?? '';
  };

  watch(sessionId, (next) => syncDraft(next), { immediate: true });

  watch(draft, (value) => {
    const current = sessionId();
    if (!current) return;
    localStorage.setItem(storageKeys.draft(current), value);
  });

  const clearDraft = () => {
    const current = sessionId();
    if (current) {
      localStorage.removeItem(storageKeys.draft(current));
    }
    draft.value = '';
  };

  return {
    draft,
    clearDraft,
    syncDraft,
  };
};