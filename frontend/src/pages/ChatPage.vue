<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import html2canvas from 'html2canvas';
import ComposerBox from '../components/chat/ComposerBox.vue';
import DocumentManager from '../components/chat/DocumentManager.vue';
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

const authHeaders = (): Record<string, string> => {
  const token = (() => {
    try {
      const raw = localStorage.getItem('ai-chat-mvp:token');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  })();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

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
  resetSessions,
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
  tokenStats,
  clearAgentState,
  clearTokenStats,
  resetMessages,
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
  handleRetryDocument,
  resetDocuments,
} = useSettings();
const { draft, clearDraft } = useComposer(() => currentSessionId.value);

// 欢迎页场景模板
const welcomeTemplates = ref<Array<{id: string; emoji: string; title: string; description: string; msg: string}>>([
  { id: 'write', emoji: '✍️', title: '写作助手', description: '写文章、邮件、报告', msg: '请帮我写一篇关于人工智能发展的简短文章，适合初学者阅读' },
  { id: 'code', emoji: '💻', title: '编程助手', description: '写代码、Debug、优化', msg: '请用 Python 写一个快速排序算法，并解释它的工作原理' },
  { id: 'translate', emoji: '🌐', title: '翻译', description: '中英互译、润色', msg: '请帮我把这段中文翻译成英文："人工智能正在改变世界"' },
  { id: 'summary', emoji: '📝', title: '总结', description: '提炼要点、归纳内容', msg: '请解释什么是 RAG（检索增强生成），它的工作原理是什么' },
  { id: 'brainstorm', emoji: '💡', title: '头脑风暴', description: '创意灵感、方案策划', msg: '我想做一个 AI 聊天应用，请帮我 brainstorm 一些核心功能和亮点' },
  { id: 'learn', emoji: '📖', title: '学习助手', description: '概念解释、知识问答', msg: '请用通俗易懂的方式解释什么是数据库索引，为什么它能加速查询' },
]);
const applyWelcomeTemplate = async (t: typeof welcomeTemplates.value[0]) => {
  draft.value = t.msg;
  // 如果模板有对应的 system prompt，应用它
  try {
    const res = await fetch(`${API_BASE}/templates`);
    if (res.ok) {
      const templates = await res.json();
      const match = templates.find((tmpl: any) => tmpl.title === t.title);
      if (match) {
        updateSettings({ ...settings.value, systemPrompt: match.system_prompt || settings.value.systemPrompt });
      }
    }
  } catch { /* ignore */ }
};

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

const loadCurrentWorkspace = async () => {
  await loadSessions();
  await loadDocuments();
  if (sessions.value.length === 0) {
    await createNewSession();
    await loadSessions();
  }
};

const resetCurrentWorkspace = () => {
  resetMessages();
  resetSessions();
  resetDocuments();
};

let recoveringExpiredAuth = false;
const handleAuthExpired = async () => {
  if (recoveringExpiredAuth) return;
  recoveringExpiredAuth = true;
  resetCurrentWorkspace();
  logout();
  try {
    if (await guestLogin()) {
      await loadCurrentWorkspace();
      toast.info('登录已过期，已切换到游客模式');
    }
  } finally {
    recoveringExpiredAuth = false;
  }
};

onMounted(async () => {
  window.addEventListener('ai-chat:auth-expired', handleAuthExpired);
  if (!user.value) {
    await guestLogin();
  }
  await loadCurrentWorkspace();
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

const handleLoggedIn = async () => {
  showLoginModal.value = false;
  resetCurrentWorkspace();
  await loadCurrentWorkspace();
  toast.success('登录成功');
};

const handleLogout = async () => {
  resetCurrentWorkspace();
  logout();
  try {
    await guestLogin();
    await loadCurrentWorkspace();
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

// 导出对话为图片
const isExportingImage = ref(false);
const isSharing = ref(false);
const showExportMenu = ref(false);
const showDocumentManager = ref(false);
// 点击空白关闭导出菜单
const closeExportMenu = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  if (!target.closest('.export-dropdown')) showExportMenu.value = false;
};
onMounted(() => document.addEventListener('click', closeExportMenu));
onUnmounted(() => {
  document.removeEventListener('click', closeExportMenu);
  window.removeEventListener('ai-chat:auth-expired', handleAuthExpired);
});

// 分享对话
const handleShare = async () => {
  if (!currentSessionId.value) return;
  isSharing.value = true;
  try {
    const res = await fetch(`${API_BASE}/sessions/${currentSessionId.value}/share`, {
      method: 'POST',
      headers: { ...authHeaders() },
    });
    if (!res.ok) throw new Error('分享失败');
    const data = await res.json();
    const shareUrl = `${window.location.origin}${data.shareUrl}`;
    await navigator.clipboard.writeText(shareUrl);
    toast.success('分享链接已复制到剪贴板');
  } catch {
    toast.error('分享失败');
  } finally {
    isSharing.value = false;
  }
};
const handleExportImage = async () => {
  if (!messages.value.length) return;
  isExportingImage.value = true;
  try {
    const stageEl = document.querySelector('.chat-stage');
    if (!stageEl) return;
    const canvas = await html2canvas(stageEl as HTMLElement, {
      backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-primary').trim() || '#ffffff',
      scale: 2,
      useCORS: true,
      logging: false,
    });
    const link = document.createElement('a');
    link.download = `chat-export-${sessionInfo.value?.title || '对话'}-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    toast.success('对话已导出为图片');
  } catch {
    toast.error('图片导出失败');
  } finally {
    isExportingImage.value = false;
  }
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
          <div class="export-dropdown">
            <button class="icon-button" title="导出对话" :disabled="!hasMessages" @click="showExportMenu = !showExportMenu">
              ⬇
            </button>
            <div v-if="showExportMenu" class="export-dropdown__menu" @click="showExportMenu = false">
              <button class="export-dropdown__item" @click="handleExport" :disabled="!hasMessages">
                <span>📝</span> Markdown
              </button>
              <button class="export-dropdown__item" @click="handleExportImage" :disabled="!hasMessages || isExportingImage">
                <span>🖼</span> 图片
              </button>
            </div>
          </div>
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
          @share="handleShare"
        />
        <div v-else class="empty-stage">
          <div class="empty-stage__welcome">
            <h2>👋 开始对话</h2>
            <p class="empty-stage__sub">选择一个场景开始，或直接输入你的问题</p>
          </div>
          <div class="empty-stage__quick-actions">
            <button
              v-for="t in welcomeTemplates"
              :key="t.id"
              class="quick-action-card"
              @click="applyWelcomeTemplate(t)"
            >
              <span class="quick-action-card__icon">{{ t.emoji }}</span>
              <span class="quick-action-card__title">{{ t.title }}</span>
              <span class="quick-action-card__desc">{{ t.description }}</span>
            </button>
          </div>
          <p class="empty-stage__hint">💡 右侧面板可开启 RAG 知识库、Agent 协作、Prompt 优化等增强功能</p>
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
      @open-document-manager="showDocumentManager = true"
    />

    <DocumentManager
      v-if="showDocumentManager"
      :documents="availableDocuments"
      :selected-ids="settings.documentIds"
      :is-uploading="isUploadingDocuments"
      :error="documentError"
      @close="showDocumentManager = false"
      @upload="handleUploadDocuments"
      @remove="handleRemoveDocument"
      @retry="handleRetryDocument"
      @toggle="(id, checked) => {
        const next = checked
          ? [...new Set([...settings.documentIds, id])]
          : settings.documentIds.filter(d => d !== id);
        updateSettings({ ...settings, documentIds: next });
      }"
    />

    <TelemetryPanel
      :telemetry="telemetry"
      :token-stats="tokenStats"
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
