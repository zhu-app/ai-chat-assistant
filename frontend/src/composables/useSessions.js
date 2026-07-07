import { computed, ref } from 'vue';
import { createSession, deleteSession, listSessions, renameSession } from '../services/chat';
import { storageKeys } from '../utils/storage';
export const useSessions = () => {
    const sessions = ref([]);
    const currentSessionId = ref(localStorage.getItem(storageKeys.currentSessionId));
    const isLoading = ref(false);
    const currentSession = computed(() => sessions.value.find((session) => session.id === currentSessionId.value) ?? null);
    const persistCurrent = (sessionId) => {
        currentSessionId.value = sessionId;
        if (sessionId) {
            localStorage.setItem(storageKeys.currentSessionId, sessionId);
        }
        else {
            localStorage.removeItem(storageKeys.currentSessionId);
        }
    };
    const loadSessions = async () => {
        isLoading.value = true;
        try {
            sessions.value = await listSessions();
            if (!currentSessionId.value && sessions.value[0]) {
                persistCurrent(sessions.value[0].id);
            }
        }
        finally {
            isLoading.value = false;
        }
    };
    const createNewSession = async () => {
        const session = await createSession();
        sessions.value = [session, ...sessions.value];
        persistCurrent(session.id);
        return session;
    };
    const renameCurrentSession = async (sessionId, title) => {
        const session = await renameSession(sessionId, title);
        const rest = sessions.value.filter((item) => item.id !== session.id);
        sessions.value = [session, ...rest];
        if (currentSessionId.value === session.id)
            persistCurrent(session.id);
        return session;
    };
    const selectSession = (sessionId) => {
        persistCurrent(sessionId);
    };
    const removeSession = async (sessionId) => {
        await deleteSession(sessionId);
        sessions.value = sessions.value.filter((item) => item.id !== sessionId);
        if (currentSessionId.value === sessionId) {
            persistCurrent(sessions.value[0]?.id ?? null);
        }
    };
    const upsertSession = (session) => {
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
    };
};
