<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { ChatSession } from '../../types/chat';
import type { AuthUser } from '../../composables/useAuth';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

const props = defineProps<{
  sessions: ChatSession[];
  currentSessionId: string | null;
  user: AuthUser | null;
}>();

const emit = defineEmits<{
  create: [];
  select: [sessionId: string];
  remove: [sessionId: string];
  rename: [sessionId: string, title: string];
  close: [];
  login: [];
  logout: [];
}>();

const searchQuery = ref('');
const hasSessions = computed(() => props.sessions.length > 0);
const isSearching = ref(false);
const searchResults = ref<ChatSession[] | null>(null);

const authHeaders = (): Record<string, string> => {
  const token = (() => {
    try {
      const raw = localStorage.getItem('ai-chat-mvp:token');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  })();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout> | null = null;
watch(searchQuery, (val) => {
  if (searchTimer) clearTimeout(searchTimer);
  if (!val.trim()) {
    searchResults.value = null;
    return;
  }
  isSearching.value = true;
  searchTimer = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions/search?q=${encodeURIComponent(val.trim())}`, {
        headers: { ...authHeaders() },
      });
      if (res.ok) {
        const data = await res.json();
        // 转换为 ChatSession 格式
        searchResults.value = data.map((item: any) => ({
          id: item.id,
          title: item.title,
          model: item.model || 'glm-4-flash',
          systemPrompt: item.system_prompt || '',
          temperature: item.temperature ?? 0.7,
          createdAt: item.created_at,
          updatedAt: item.updated_at,
        }));
      }
    } catch { /* ignore */ }
    isSearching.value = false;
  }, 300);
});

const displaySessions = computed(() => {
  if (searchResults.value !== null) return searchResults.value;
  return props.sessions;
});

const apiSearchQuery = computed(() => searchQuery.value.trim());

const editingId = ref<string | null>(null);
const editTitle = ref('');

const startRename = (sessionId: string, currentTitle: string) => {
  editingId.value = sessionId;
  editTitle.value = currentTitle;
};

const saveRename = () => {
  if (editingId.value && editTitle.value.trim()) {
    emit('rename', editingId.value, editTitle.value.trim());
  }
  editingId.value = null;
};

const cancelRename = () => {
  editingId.value = null;
};

const formatTime = (iso: string) => {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin} 分钟前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} 小时前`;
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar__header">
      <div class="sidebar__brand">
        <span class="sidebar__brand-icon">✦</span>
        <span class="sidebar__brand-text">知聊</span>
      </div>
      <div class="sidebar__header-actions">
        <button class="ghost-button" @click="emit('create')">新建</button>
        <button class="sidebar__icon-btn sidebar__close-btn" @click="emit('close')" title="关闭侧栏">✕</button>
      </div>
    </div>

    <!-- 搜索框 -->
    <div v-if="hasSessions" class="sidebar__search">
      <input
        v-model="searchQuery"
        class="sidebar__search-input"
        type="text"
        placeholder="搜索对话…"
      />
    </div>

    <div v-if="hasSessions" class="session-list">
      <div v-if="isSearching" class="session-list__searching">搜索中…</div>
      <div
        v-for="session in displaySessions"
        :key="session.id"
        class="session-card"
        :class="{ 'session-card--active': session.id === currentSessionId }"
        @click="emit('select', session.id)"
      >
        <div class="session-card__main">
          <!-- 编辑模式 -->
          <input
            v-if="editingId === session.id"
            class="session-card__edit-input"
            v-model="editTitle"
            @click.stop
            @keydown.enter.prevent="saveRename"
            @keydown.escape.prevent="cancelRename"
            @blur="saveRename"
            ref="editInput"
            autofocus
          />
          <!-- 显示模式 -->
          <strong v-else>{{ session.title }}</strong>
          <span>{{ session.model }}</span>
        </div>
        <div class="session-card__meta">
          <span class="session-card__time">{{ formatTime(session.updatedAt) }}</span>
        </div>
        <div class="session-card__actions">
          <span class="session-card__action" @click.stop="startRename(session.id, session.title)">重命名</span>
          <span class="session-card__action session-card__action--danger" @click.stop="emit('remove', session.id)">
            删除
          </span>
        </div>
      </div>
    </div>

    <div v-else class="empty-panel">
      <p>还没有对话</p>
      <small>发起新对话后，左侧会自动生成会话列表</small>
    </div>

    <!-- 底部用户信息 -->
    <div v-if="user" class="sidebar__user">
      <div class="sidebar__user-avatar">{{ user.username.charAt(0).toUpperCase() }}</div>
      <span class="sidebar__user-name">{{ user.username }}</span>
      <div class="sidebar__user-actions">
        <button
          v-if="user.username.startsWith('游客')"
          class="sidebar__user-login"
          @click="emit('login')"
          title="登录/注册"
        >登录</button>
        <button
          v-else
          class="sidebar__user-logout"
          @click="emit('logout')"
          title="退出登录"
        >退出</button>
      </div>
    </div>
  </aside>
</template>