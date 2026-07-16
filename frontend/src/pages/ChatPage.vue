<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import ComposerBox from '../components/chat/ComposerBox.vue';
import MessageList from '../components/chat/MessageList.vue';
import SessionSidebar from '../components/chat/SessionSidebar.vue';
import SettingsPanel from '../components/chat/SettingsPanel.vue';
import TelemetryPanel from '../components/chat/TelemetryPanel.vue';
import LoginModal from '../components/LoginModal.vue';
import { useAuth } from '../composables/useAuth';
import { useComposer } from '../composables/useComposer';
import { useMessages } from '../composables/useMessages';
import { useSessions } from '../composables/useSessions';
import { useSettings } from '../composables/useSettings';
import { useToast } from '../composables/useToast';
import { readJson, writeJson } from '../utils/storage';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '');

const { user, guestLogin, logout } = useAuth();
const showLoginModal = ref(false);
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
const {
  messages,
  hasMessages,
  isStreaming,
  error,
  loadMessages,
  sendMessage,
  stopStream,
  agentPlan,
  agentSteps,
  agentReview,
  promptOptimize,
  telemetry,
  clearAgentState,
} = useMessages();
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

// 检测后端是否为模拟模式（未配置 API Key）
const mockMode = ref(false);

// Telemetry 面板 — 不自动弹出，用小红点提示有新数据
const showTelemetry = ref(false);
const hasTelemetry = computed(() => telemetry.value !== null);
const hasNewTelemetry = ref(false);

// 主题切换
const theme = ref<'dark' | 'light'>(readJson<'dark' | 'light'>('ai-chat-mvp:theme', 'light'));
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
    clearAgentState();
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
  // 未登录用户自动以游客模式进入
  if (!user.value) {
    await guestLogin();
  }
  await loadSessions();
  await loadDocuments();
  // 新用户没有会话时，自动创建一个新对话
  if (sessions.value.length === 0) {
    await createNewSession();
    await loadSessions();
  }
  document.documentElement.setAttribute('data-theme', theme.value);

  // 检测后端是否为模拟模式
  try {
    const res = await fetch(`${API_BASE}/health/ready`);
    if (res.ok) {
      const data = await res.json();
      if (data.checks?.llm?.remote_enabled === false) {
        mockMode.value = true;
      }
    }
  } catch { /* ignore */ }
});

// Telemetry 新数据到达 → 标记小红点，不自动弹窗
watch(telemetry, (val) => {
  if (val) {
    hasNewTelemetry.value = true;
  }
});

const updateDraft = (value: string) => {
  draft.value = value;
};

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
};

const handleCreateSession = async () => {
  if (isStreaming.value) stopStream();

  // 如果当前会话还没有任何消息，不创建新会话，直接复用
  if (currentSessionId.value && messages.value.length === 0) {
    toast.info('当前对话为空，直接使用即可');
    return;
  }

  try {
    await createNewSession();
    await loadSessions();
    clearAgentState();
  } catch (e) {
    toast.error('创建对话失败');
    return;
  }
  toast.success('已创建新对话');
};

const handleSelectSession = (sessionId: string) => {
  if (isStreaming.value) stopStream();
  selectSession(sessionId);
  clearAgentState();
};

const handleRenameSession = async (sessionId: string, title: string) => {
  if (!title.trim()) return;
  await renameCurrentSession(sessionId, title.trim());
  toast.success('已重命名');
};

const runSend = async (content: string) => {
  const sessionId = currentSessionId.value;
  clearAgentState();
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

const handleSend = () => {
  const content = draft.value.trim();
  if (!content || isStreaming.value) return;

  // 立刻清空输入框，不等异步结束
  draft.value = '';

  runSend(content);
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

  // 重试时不清除旧消息，而是让新生成的消息自然覆盖（服务器端不保留删除逻辑）
  // 旧消息保留在列表中，新消息会追加在后面，用户可手动删除旧会话
  // 更好的方案：在服务端添加删除消息 API，但简单场景下直接清空当前会话最后一条 assistant 消息即可
  const lastAssistantIndex = (() => {
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i]?.role === 'assistant') return i;
    }
    return -1;
  })();

  if (lastAssistantIndex >= 0 && lastAssistantIndex === messageIndex) {
    // 只移除最后一条 assistant 消息（当前正在重试的），保留 user 消息
    messages.value = messages.value.filter((_, i) => i !== messageIndex);
  }

  draft.value = retryContent;
  await runSend(retryContent);
};

// 应用 Prompt 模板
const handleApplyTemplate = (systemPrompt: string, suggestedMessage: string) => {
  updateSettings({ ...settings.value, systemPrompt: systemPrompt });
  if (suggestedMessage) {
    draft.value = suggestedMessage;
  }
};

// 登录 / 退出
const handleLogin = () => {
  showLoginModal.value = true;
};

const handleLoggedIn = () => {
  showLoginModal.value = false;
  toast.success('登录成功');
};

const handleLogout = async () => {
  logout();
  try {
    await guestLogin();
    await loadSessions();
    toast.info('已切换到游客模式');
  } catch {
    // 游客模式失败不影响使用
  }
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
      @login="handleLogin"
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
          <button
            class="icon-button telemetry-btn"
            :class="{ 'icon-button--active': showTelemetry && hasTelemetry }"
            title="响应分析"
            :disabled="!hasTelemetry"
            @click="showTelemetry = !showTelemetry; hasNewTelemetry = false"
          >
            📊
            <span v-if="hasNewTelemetry" class="telemetry-btn__dot" />
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
        <MessageList
          v-if="hasMessages || agentSteps.length > 0"
          :messages="messages"
          :agent-plan="agentPlan"
          :agent-steps="agentSteps"
          :agent-review="agentReview"
          :prompt-optimize="promptOptimize"
          :is-streaming="isStreaming"
          :enable-prompt-optimizer="settings.enablePromptOptimizer"
          @retry="handleRetry"
        />
        <div v-else class="empty-stage">
          <h3>输入你的第一个问题</h3>
          <p>上传文档后，勾选右侧知识库文档并启用 RAG，就能基于文档进行问答。</p>
          <p class="empty-stage__hint">还可开启 ✨ Prompt 优化 或 🤖 Agent 协作模式体验更强大的能力。</p>
        </div>
      </section>

      <p v-if="error" class="error-banner">{{ error }}</p>
	<p v-if="mockMode" class="warning-banner">
		⚠️ 后端未配置 API Key，当前为本地模拟模式，所有回复均为测试数据。
		<a :href="`${API_BASE}/health/ready`" target="_blank" style="color:inherit;text-decoration:underline;">查看状态</a>
	</p>
      <ComposerBox
        :value="draft"
        :is-streaming="isStreaming"
        :system-prompt="settings.systemPrompt"
        @update="updateDraft"
        @send="handleSend"
        @stop="stopStream"
        @apply-template="handleApplyTemplate"
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

    <TelemetryPanel
      :telemetry="telemetry"
      :visible="showTelemetry && hasTelemetry"
      @close="showTelemetry = false"
    />

    <LoginModal
      v-if="showLoginModal"
      @close="showLoginModal = false"
      @logged-in="handleLoggedIn"
    />
  </div>
</template>