<script setup lang="ts">
import { ref } from 'vue';
import { useAuth } from '../composables/useAuth';

const { login, register, guestLogin, authError, isLoading, isLoggedIn } = useAuth();

const emit = defineEmits<{
  loggedIn: [];
}>();

const mode = ref<'login' | 'register'>('login');
const username = ref('');
const password = ref('');
const confirmPassword = ref('');

const toggleMode = () => {
  mode.value = mode.value === 'login' ? 'register' : 'login';
  authError.value = null;
};

const handleSubmit = async () => {
  if (!username.value.trim() || !password.value) return;
  if (mode.value === 'register' && password.value !== confirmPassword.value) {
    authError.value = '两次密码不一致';
    return;
  }

  let ok: boolean;
  if (mode.value === 'login') {
    ok = await login(username.value, password.value);
  } else {
    ok = await register(username.value, password.value);
  }
  if (ok) {
    emit('loggedIn');
  }
};

const handleGuest = async () => {
  const ok = await guestLogin();
  if (ok) {
    emit('loggedIn');
  }
};
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card__header">
        <div class="login-card__icon">💬</div>
        <h1>灵知</h1>
        <p class="login-card__subtitle">智能对话 · 知识库增强</p>
      </div>

      <form class="login-card__form" @submit.prevent="handleSubmit">
        <label class="login-field">
          <span>用户名</span>
          <input
            v-model="username"
            type="text"
            placeholder="输入用户名"
            autocomplete="username"
            required
          />
        </label>

        <label class="login-field">
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            placeholder="输入密码"
            autocomplete="current-password"
            required
          />
        </label>

        <label v-if="mode === 'register'" class="login-field">
          <span>确认密码</span>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
            required
          />
        </label>

        <p v-if="authError" class="login-error">{{ authError }}</p>

        <button type="submit" class="login-button" :disabled="isLoading">
          {{ isLoading ? '请稍候…' : mode === 'login' ? '登录' : '注册' }}
        </button>
      </form>

      <div class="login-card__divider">
        <span>或</span>
      </div>

      <button class="guest-button" :disabled="isLoading" @click="handleGuest">
        👤 游客模式，立即体验
      </button>
      <small class="guest-hint">无需注册，数据保存在本地</small>

      <p class="login-card__switch">
        {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
        <button class="login-switch-btn" @click="toggleMode">
          {{ mode === 'login' ? '注册' : '登录' }}
        </button>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 40px 32px;
  box-shadow: var(--shadow-lg);
}

.login-card__header {
  text-align: center;
  margin-bottom: 32px;
}

.login-card__icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.login-card__header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.login-card__subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.login-card__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.login-field span {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.login-field input {
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease;
}

.login-field input:focus {
  border-color: var(--accent);
}

.login-error {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--danger);
  background: var(--danger-soft);
}

.login-button {
  padding: 12px;
  border: 0;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--accent-text);
  background: var(--accent);
  cursor: pointer;
  transition: background 0.15s ease;
}

.login-button:hover {
  background: var(--accent-hover);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-card__divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  color: var(--text-muted);
  font-size: 12px;
}

.login-card__divider::before,
.login-card__divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.guest-button {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  background: var(--bg-tertiary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.guest-button:hover {
  background: var(--bg-hover);
  border-color: var(--accent);
  color: var(--accent);
}

.guest-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.guest-hint {
  display: block;
  text-align: center;
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.login-card__switch {
  text-align: center;
  margin: 20px 0 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.login-switch-btn {
  background: none;
  border: 0;
  color: var(--accent);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
}

.login-switch-btn:hover {
  text-decoration: underline;
}
</style>