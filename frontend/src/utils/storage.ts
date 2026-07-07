const PREFIX = 'ai-chat-mvp';

export const storageKeys = {
  sessions: `${PREFIX}:sessions`,
  currentSessionId: `${PREFIX}:current-session-id`,
  settings: `${PREFIX}:settings`,
  token: `${PREFIX}:token`,
  user: `${PREFIX}:user`,
  draft: (sessionId: string) => `${PREFIX}:draft:${sessionId}`,
};

export const readJson = <T>(key: string, fallback: T): T => {
  const raw = localStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
};

export const writeJson = (key: string, value: unknown) => {
  localStorage.setItem(key, JSON.stringify(value));
};