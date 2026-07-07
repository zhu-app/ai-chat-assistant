const PREFIX = 'ai-chat-mvp';
export const storageKeys = {
    sessions: `${PREFIX}:sessions`,
    currentSessionId: `${PREFIX}:current-session-id`,
    settings: `${PREFIX}:settings`,
    token: `${PREFIX}:token`,
    user: `${PREFIX}:user`,
    draft: (sessionId) => `${PREFIX}:draft:${sessionId}`,
};
export const readJson = (key, fallback) => {
    const raw = localStorage.getItem(key);
    if (!raw)
        return fallback;
    try {
        return JSON.parse(raw);
    }
    catch {
        return fallback;
    }
};
export const writeJson = (key, value) => {
    localStorage.setItem(key, JSON.stringify(value));
};
