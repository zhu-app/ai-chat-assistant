import { computed, ref } from 'vue';
import { readJson, storageKeys, writeJson } from '../utils/storage';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

export interface AuthUser {
  userId: string;
  username: string;
}

const token = ref<string | null>(readJson<string | null>(storageKeys.token, null));
const user = ref<AuthUser | null>(readJson<AuthUser | null>(storageKeys.user, null));
const authError = ref<string | null>(null);
const isLoading = ref(false);

export const useAuth = () => {
  const isLoggedIn = computed(() => !!token.value && !!user.value);

  const apiHeaders = () => ({
    'Content-Type': 'application/json',
    ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
  });

  const login = async (username: string, password: string): Promise<boolean> => {
    authError.value = null;
    isLoading.value = true;
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        authError.value = data.detail || '登录失败';
        return false;
      }
      token.value = data.token;
      user.value = { userId: data.user_id, username: data.username };
      writeJson(storageKeys.token, data.token);
      writeJson(storageKeys.user, { userId: data.user_id, username: data.username });
      return true;
    } catch {
      authError.value = '网络错误，请检查连接';
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const register = async (username: string, password: string): Promise<boolean> => {
    authError.value = null;
    isLoading.value = true;
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        authError.value = data.detail || '注册失败';
        return false;
      }
      token.value = data.token;
      user.value = { userId: data.user_id, username: data.username };
      writeJson(storageKeys.token, data.token);
      writeJson(storageKeys.user, { userId: data.user_id, username: data.username });
      return true;
    } catch {
      authError.value = '网络错误，请检查连接';
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const guestLogin = async (): Promise<boolean> => {
    authError.value = null;
    isLoading.value = true;
    try {
      const res = await fetch(`${API_BASE}/auth/guest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) {
        authError.value = data.detail || '游客模式启动失败';
        return false;
      }
      token.value = data.token;
      user.value = { userId: data.user_id, username: data.username };
      writeJson(storageKeys.token, data.token);
      writeJson(storageKeys.user, { userId: data.user_id, username: data.username });
      return true;
    } catch {
      authError.value = '网络错误，请检查连接';
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = () => {
    token.value = null;
    user.value = null;
    localStorage.removeItem(storageKeys.token);
    localStorage.removeItem(storageKeys.user);
  };

  return {
    token,
    user,
    isLoggedIn,
    authError,
    isLoading,
    apiHeaders,
    login,
    register,
    guestLogin,
    logout,
  };
};