<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import ComposerBox from '../components/chat/ComposerBox.vue';
import MessageList from '../components/chat/MessageList.vue';
import SessionSidebar from '../components/chat/SessionSidebar.vue';
import SettingsPanel from '../components/chat/SettingsPanel.vue';
import { useAuth } from '../composables/useAuth';
import { useComposer } from '../composables/useComposer';
import { useMessages } from '../composables/useMessages';
import { useSessions } from '../composables/useSessions';
import { useSettings } from '../composables/useSettings';
import { useToast } from '../composables/useToast';
import { readJson, writeJson } from '../utils/storage';

const emit = defineEmits<{
  logout: [];
}>();

const { user, logout } = useAuth();
const toast = useToast();

const {
  sessions,
  currentSessionId,
  currentSession,
  loadSessions,
  createNewSession,
  renameCurrentSession,
  selectSession,
  removeSession,
  upsertSession,
} = useSessions();
const { messages, hasMessages, isStreaming, error, loadMessages, sendMessage, stopStream } = useMessages();
const {
  settings,
  availableDocuments,
  isUploadingDocuments,
  documentError,
  updateSettings,
  loadDocuments,
  handleUploadDocuments,
  handleDeleteDocument,
} = useSettings();
const { draft, clearDraft } = useComposer(() => currentSessionId.value);

// 当前会话的本地引用（解决 vue-tsc ComputedRef 类型推断问题）
const sessionInfo = computed(() => currentSession.value);

// 侧栏折叠状态（默认展开，点击 ✕ 折叠）
const sidebarCollapsed = ref(false);
const settingsOpen = ref(false);

// 主题切换
const theme = ref<'dark' | 'light'>(readJson<'dark' | 'light'>('ai-chat-mvp:theme', 'dark'));
const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
  writeJson('ai-chat-mvp:theme', theme.value);
  document.documentElement.setAttribute('data-theme', theme.value);
};

const selectedDocumentNames = computed(() =>
  availableDocuments.value
    .filter((document) => settings.value.documentIds.includes(document.id))
    .map((document) => document.filename),
);

watch(
  currentSessionId,
  (sessionId) => {
    loadMessages(sessionId);
    // 切换会话时，加载该会话保存的 model/systemPrompt/temperature
    if (sessionId) {
      const session = sessions.value.find((s) => s.id === sessionId);
      if (session) {
        updateSettings({
          ...settings.value,
          model: session.model || settings.value.model,
          systemPrompt: session.systemPrompt || settings.value.systemPrompt,
          temperature: session.temperature ?? settings.value.temperature,
        });
      }
    }
  },
  { immediate: true },
);

onMounted(async () => {
  await loadSessions();
  await loadDocuments();
  // 新用户没有会话时，自动创建一个新对话
  if (sessions.value.length === 0) {
    await handleCreateSession();
  }
  document.documentElement.setAttribute('data-theme', theme.value);
});

const updateDraft = (value: string) => {
  draft.value = value;
};

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
};

const handleCreateSession = async () => {
  if (isStreaming.value) stopStream();
  await createNewSession();
  toast.success('已创建新对话');
};

const handleSelectSession = (sessionId: string) => {
  if (isStreaming.value) stopStream();
  selectSession(sessionId);
};

const handleRenameSession = async (sessionId: string, title: string) => {
  if (!title.trim()) return;
  await renameCurrentSession(sessionId, title.trim());
  toast.success('已重命名');
};

const runSend = async (content: string) => {
  const sessionId = currentSessionId.value;
  await sendMessage(
    {
      sessionId,
      message: content,
      settings: settings.value,
    },
    (newSessionId, title) => {
      upsertSession({
        id: newSessionId,
        title: title ?? '新对话',
        model: settings.value.model,
        systemPrompt: settings.value.systemPrompt,
        temperature: settings.value.temperature,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      });
    },
  );

  await loadSessions();
  if (sessionId) await loadMessages(sessionId);
};

const handleSend = async () => {
  const content = draft.value.trim();
  if (!content) return;

  await runSend(content);
  clearDraft();
};

const handleRemoveSession = async (sessionId: string) => {
  if (!window.confirm('确定要删除这个对话吗？删除后无法恢复。')) return;
  await removeSession(sessionId);
  toast.success('对话已删除');
};

const handleRemoveDocument = async (documentId: string) => {
  if (!window.confirm('确定要删除这个文档吗？')) return;
  await handleDeleteDocument(documentId);
  toast.success('文档已删除');
};

const handleRetry = async (messageId: string) => {
  const messageIndex = messages.value.findIndex((message) => message.id === messageId);
  if (messageIndex <= 0) return;

  // 找到紧挨着这条 assistant 消息前面的 user 消息（真正的配对）
  const userIndex = (() => {
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages.value[i]?.role === 'user') return i;
    }
    return -1;
  })();
  if (userIndex < 0) return;

  const retryContent = messages.value[userIndex]?.content;
  if (!retryContent) return;

  // 移除旧的失败消息对（user + assistant）
  const removeIds = [messages.value[userIndex]?.id, messageId].filter(Boolean);
  const oldMessages = messages.value;
  messages.value = messages.value.filter((m) => !removeIds.includes(m.id));
  // 如果删除后数组没变，说明消息不在列表中，恢复原样
  if (messages.value.length === oldMessages.length) {
    messages.value = oldMessages;
  }

  draft.value = retryContent;
  await runSend(retryContent);
};

// 退出登录
const handleLogout = () => {
  logout();
  emit('logout');
};

// 导出对话为 Markdown
const handleExport = () => {
  if (!messages.value.length) return;
  toast.success('对话已导出');
  const lines = messages.value.map((m) => {
    const role = m.role === 'user' ? '**你**' : '**AI**';
    return `## ${role}\n\n${m.content}\n\n---\n`;
  });
  const header = `# 对话导出\n\n> 导出时间: ${new Date().toLocaleString()}\n\n${sessionInfo.value?.title ? `> 会话: ${sessionInfo.value.title}\n\n` : '\n'}`;
  const markdown = header + lines.join('\n');

  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `chat-export-${sessionInfo.value?.title || '对话'}-${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
};
</script>

<template>
  <div class="chat-layout" :class="{ 'chat-layout--sidebar-collapsed': sidebarCollapsed, 'chat-layout--settings-open': settingsOpen }">
    <!-- 移动端遮罩 -->
    <div v-if="settingsOpen" class="overlay" @click="settingsOpen = false" />

    <!-- 侧边栏 -->
    <SessionSidebar
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :user="user"
      @create="handleCreateSession"
      @select="handleSelectSession"
      @rename="handleRenameSession"
      @remove="handleRemoveSession"
      @close="sidebarCollapsed = true"
      @logout="handleLogout"
    />

    <main class="chat-main">
      <header class="chat-header">
        <div class="chat-header__left">
          <!-- 移动端菜单按钮 -->
          <button class="chat-header__menu-btn" @click="toggleSidebar" title="切换会话列表">
            ☰
          </button>
          <div>
            <p class="chat-header__eyebrow">当前会话</p>
            <h2>{{ sessionInfo?.title || '准备开始新的对话' }}</h2>
            <p class="chat-header__subline">
              {{
                settings.useRag
                  ? selectedDocumentNames.length
                    ? `当前检索范围：${selectedDocumentNames.join('、')}`
                    : 'RAG 已启用，但当前还没有选中文档。'
                  : '当前为普通聊天模式。'
              }}
            </p>
          </div>
        </div>
        <div class="chat-header__right">
          <button class="icon-button" title="导出对话" @click="handleExport" :disabled="!hasMessages">
            ⬇
          </button>
          <button class="icon-button" title="切换主题" @click="toggleTheme">
            {{ theme === 'dark' ? '☀' : '🌙' }}
          </button>
          <button class="chat-header__settings-btn" title="打开设置" @click="settingsOpen = !settingsOpen">
            ⚙
          </button>
          <div class="chat-header__status" :class="{ 'chat-header__status--live': isStreaming }">
            {{ isStreaming ? '生成中' : '就绪' }}
          </div>
        </div>
      </header>

      <section class="chat-stage">
        <MessageList v-if="hasMessages" :messages="messages" @retry="handleRetry" />
        <div v-else class="empty-stage">
          <h3>输入你的第一个问题</h3>
          <p>上传文档后，勾选右侧知识库文档并启用 RAG，就能基于文档进行问答。</p>
        </div>
      </section>

      <p v-if="error" class="error-banner">{{ error }}</p>
      <ComposerBox
        :value="draft"
        :is-streaming="isStreaming"
        @update="updateDraft"
        @send="handleSend"
        @stop="stopStream"
      />
    </main>

    <SettingsPanel
      :settings="settings"
      :documents="availableDocuments"
      :is-uploading-documents="isUploadingDocuments"
      :document-error="documentError"
      @update="updateSettings"
      @upload="handleUploadDocuments"
      @remove-document="handleRemoveDocument"
    />
  </div>
</template>