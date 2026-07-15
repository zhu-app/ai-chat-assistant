<script setup lang="ts">
import { ref } from 'vue';
import { useAuth } from '../composables/useAuth';

const { login, register, authError, isLoading } = useAuth();

const emit = defineEmits<{
  close: [];
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

const handleBackdrop = () => {
  emit('close');
};
</script>

<template>
  <div class="login-overlay" @click.self="handleBackdrop">
    <div class="login-dialog">
      <button class="login-dialog__close" @click="emit('close')">✕</button>
      <div class="login-dialog__header">
        <h2>{{ mode === 'login' ? '登录' : '注册' }}</h2>
        <p class="login-dialog__subtitle">登录后可同步数据到云端</p>
      </div>
      <form class="login-dialog__form" @submit.prevent="handleSubmit">
        <label class="login-field">
          <span>用户名</span>
          <input v-model="username" type="text" placeholder="输入用户名" autocomplete="username" required />
        </label>
        <label class="login-field">
          <span>密码</span>
          <input v-model="password" type="password" placeholder="输入密码" autocomplete="current-password" required />
        </label>
        <label v-if="mode === 'register'" class="login-field">
          <span>确认密码</span>
          <input v-model="confirmPassword" type="password" placeholder="再次输入密码" autocomplete="new-password" required />
        </label>
        <p v-if="authError" class="login-error">{{ authError }}</p>
        <button type="submit" class="login-button" :disabled="isLoading">
          {{ isLoading ? '请稍候…' : mode === 'login' ? '登录' : '注册并登录' }}
        </button>
      </form>
      <p class="login-dialog__switch">
        {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
        <button class="login-switch-btn" @click="toggleMode">
          {{ mode === 'login' ? '注册' : '登录' }}
        </button>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-overlay { position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; padding: 20px; animation: fadeIn 0.15s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.login-dialog { width: 100%; max-width: 380px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 16px; padding: 32px 28px; box-shadow: var(--shadow-lg); position: relative; animation: slideUp 0.2s ease; }
@keyframes slideUp { from { transform: translateY(12px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.login-dialog__close { position: absolute; top: 12px; right: 12px; background: none; border: 0; font-size: 16px; color: var(--text-muted); cursor: pointer; padding: 4px 8px; border-radius: 6px; }
.login-dialog__close:hover { background: var(--bg-hover); color: var(--text-primary); }
.login-dialog__header { text-align: center; margin-bottom: 24px; }
.login-dialog__header h2 { margin: 0 0 6px; font-size: 20px; font-weight: 700; color: var(--text-primary); }
.login-dialog__subtitle { margin: 0; font-size: 13px; color: var(--text-muted); }
.login-dialog__form { display: flex; flex-direction: column; gap: 14px; }
.login-field { display: flex; flex-direction: column; gap: 5px; }
.login-field span { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.login-field input { padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-tertiary); color: var(--text-primary); font-size: 14px; outline: none; transition: border-color 0.2s ease; }
.login-field input:focus { border-color: var(--accent); }
.login-error { margin: 0; padding: 8px 10px; border-radius: 6px; font-size: 13px; color: var(--danger); background: var(--danger-soft); }
.login-button { padding: 10px; border: 0; border-radius: 8px; font-size: 14px; font-weight: 600; color: var(--accent-text); background: var(--accent); cursor: pointer; transition: background 0.15s ease; }
.login-button:hover { background: var(--accent-hover); }
.login-button:disabled { opacity: 0.6; cursor: not-allowed; }
.login-dialog__switch { text-align: center; margin: 16px 0 0; font-size: 13px; color: var(--text-secondary); }
.login-switch-btn { background: none; border: 0; color: var(--accent); font-size: 13px; font-weight: 500; cursor: pointer; padding: 0; }
.login-switch-btn:hover { text-decoration: underline; }
</style>