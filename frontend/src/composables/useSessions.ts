import { computed, ref } from 'vue';
import { createSession, deleteSession, listSessions, renameSession } from '../services/chat';
import type { ChatSession } from '../types/chat';
import { storageKeys } from '../utils/storage';

export const useSessions = () => {
  const sessions = ref<ChatSession[]>([]);
  const currentSessionId = ref<string | null>(localStorage.getItem(storageKeys.currentSessionId));
  const isLoading = ref(false);
  let loadVersion = 0;

  const currentSession = computed(() =>
    sessions.value.find((session) => session.id === currentSessionId.value) ?? null,
  );

  const persistCurrent = (sessionId: string | null) => {
    currentSessionId.value = sessionId;
    if (sessionId) {
      localStorage.setItem(storageKeys.currentSessionId, sessionId);
    } else {
      localStorage.removeItem(storageKeys.currentSessionId);
    }
  };

  const loadSessions = async () => {
    const version = ++loadVersion;
    isLoading.value = true;
    try {
      let loaded: ChatSession[];
      try {
        loaded = await listSessions();
      } catch (reason) {
        if (version !== loadVersion) return;
        throw reason;
      }
      if (version !== loadVersion) return;
      sessions.value = loaded;
      if (!sessions.value.some((session) => session.id === currentSessionId.value)) {
        persistCurrent(sessions.value[0]?.id ?? null);
      }
    } finally {
      if (version === loadVersion) isLoading.value = false;
    }
  };

  const resetSessions = () => {
    loadVersion += 1;
    sessions.value = [];
    isLoading.value = false;
    persistCurrent(null);
  };

  const createNewSession = async () => {
    const session = await createSession();
    sessions.value = [session, ...sessions.value];
    persistCurrent(session.id);
    return session;
  };

  const renameCurrentSession = async (sessionId: string, title: string) => {
    const session = await renameSession(sessionId, title);
    const rest = sessions.value.filter((item) => item.id !== session.id);
    sessions.value = [session, ...rest];
    if (currentSessionId.value === session.id) persistCurrent(session.id);
    return session;
  };

  const selectSession = (sessionId: string) => {
    persistCurrent(sessionId);
  };

  const removeSession = async (sessionId: string) => {
    await deleteSession(sessionId);
    sessions.value = sessions.value.filter((item) => item.id !== sessionId);
    if (currentSessionId.value === sessionId) {
      persistCurrent(sessions.value[0]?.id ?? null);
    }
  };

  const upsertSession = (session: ChatSession) => {
    const rest = sessions.value.filter((item) => item.id !== session.id);
    sessions.value = [session, ...rest];
    persistCurrent(session.id);
  };

  return {
    sessions,
    currentSessionId,
    currentSession,
    isLoading,
    loadSessions,
    createNewSession,
    renameCurrentSession,
    selectSession,
    removeSession,
    upsertSession,
    resetSessions,
  };
};
