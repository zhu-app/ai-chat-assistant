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
const emit = defineEmits();
const { user, logout } = useAuth();
const toast = useToast();
const { sessions, currentSessionId, currentSession, loadSessions, createNewSession, renameCurrentSession, selectSession, removeSession, upsertSession, } = useSessions();
const { messages, hasMessages, isStreaming, error, loadMessages, sendMessage, stopStream } = useMessages();
const { settings, availableDocuments, isUploadingDocuments, documentError, updateSettings, loadDocuments, handleUploadDocuments, handleDeleteDocument, } = useSettings();
const { draft, clearDraft } = useComposer(() => currentSessionId.value);
// 当前会话的本地引用（解决 vue-tsc ComputedRef 类型推断问题）
const sessionInfo = computed(() => currentSession.value);
// 移动端侧栏状态
const sidebarOpen = ref(false);
const settingsOpen = ref(false);
// 主题切换
const theme = ref(readJson('ai-chat-mvp:theme', 'dark'));
const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark';
    writeJson('ai-chat-mvp:theme', theme.value);
    document.documentElement.setAttribute('data-theme', theme.value);
};
const selectedDocumentNames = computed(() => availableDocuments.value
    .filter((document) => settings.value.documentIds.includes(document.id))
    .map((document) => document.filename));
watch(currentSessionId, (sessionId) => {
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
}, { immediate: true });
onMounted(async () => {
    await loadSessions();
    await loadDocuments();
    // 新用户没有会话时，自动创建一个新对话
    if (sessions.value.length === 0) {
        await handleCreateSession();
    }
    document.documentElement.setAttribute('data-theme', theme.value);
});
const updateDraft = (value) => {
    draft.value = value;
};
const handleCreateSession = async () => {
    if (isStreaming.value)
        stopStream();
    await createNewSession();
    toast.success('已创建新对话');
};
const handleSelectSession = (sessionId) => {
    if (isStreaming.value)
        stopStream();
    selectSession(sessionId);
    sidebarOpen.value = false;
};
const handleRenameSession = async (sessionId, title) => {
    if (!title.trim())
        return;
    await renameCurrentSession(sessionId, title.trim());
    toast.success('已重命名');
};
const runSend = async (content) => {
    const sessionId = currentSessionId.value;
    await sendMessage({
        sessionId,
        message: content,
        settings: settings.value,
    }, (newSessionId, title) => {
        upsertSession({
            id: newSessionId,
            title: title ?? '新对话',
            model: settings.value.model,
            systemPrompt: settings.value.systemPrompt,
            temperature: settings.value.temperature,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        });
    });
    await loadSessions();
    if (sessionId)
        await loadMessages(sessionId);
};
const handleSend = async () => {
    const content = draft.value.trim();
    if (!content)
        return;
    await runSend(content);
    clearDraft();
};
const handleRemoveSession = async (sessionId) => {
    if (!window.confirm('确定要删除这个对话吗？删除后无法恢复。'))
        return;
    await removeSession(sessionId);
    toast.success('对话已删除');
};
const handleRemoveDocument = async (documentId) => {
    if (!window.confirm('确定要删除这个文档吗？'))
        return;
    await handleDeleteDocument(documentId);
    toast.success('文档已删除');
};
const handleRetry = async (messageId) => {
    const messageIndex = messages.value.findIndex((message) => message.id === messageId);
    if (messageIndex <= 0)
        return;
    // 找到紧挨着这条 assistant 消息前面的 user 消息（真正的配对）
    const userIndex = (() => {
        for (let i = messageIndex - 1; i >= 0; i--) {
            if (messages.value[i]?.role === 'user')
                return i;
        }
        return -1;
    })();
    if (userIndex < 0)
        return;
    const retryContent = messages.value[userIndex]?.content;
    if (!retryContent)
        return;
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
    if (!messages.value.length)
        return;
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
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "chat-layout" },
    ...{ class: ({ 'chat-layout--sidebar-open': __VLS_ctx.sidebarOpen, 'chat-layout--settings-open': __VLS_ctx.settingsOpen }) },
});
if (__VLS_ctx.sidebarOpen || __VLS_ctx.settingsOpen) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.sidebarOpen || __VLS_ctx.settingsOpen))
                    return;
                __VLS_ctx.sidebarOpen = false;
                __VLS_ctx.settingsOpen = false;
            } },
        ...{ class: "overlay" },
    });
}
/** @type {[typeof SessionSidebar, ]} */ ;
// @ts-ignore
const __VLS_0 = __VLS_asFunctionalComponent(SessionSidebar, new SessionSidebar({
    ...{ 'onCreate': {} },
    ...{ 'onSelect': {} },
    ...{ 'onRename': {} },
    ...{ 'onRemove': {} },
    ...{ 'onLogout': {} },
    sessions: (__VLS_ctx.sessions),
    currentSessionId: (__VLS_ctx.currentSessionId),
    user: (__VLS_ctx.user),
}));
const __VLS_1 = __VLS_0({
    ...{ 'onCreate': {} },
    ...{ 'onSelect': {} },
    ...{ 'onRename': {} },
    ...{ 'onRemove': {} },
    ...{ 'onLogout': {} },
    sessions: (__VLS_ctx.sessions),
    currentSessionId: (__VLS_ctx.currentSessionId),
    user: (__VLS_ctx.user),
}, ...__VLS_functionalComponentArgsRest(__VLS_0));
let __VLS_3;
let __VLS_4;
let __VLS_5;
const __VLS_6 = {
    onCreate: (__VLS_ctx.handleCreateSession)
};
const __VLS_7 = {
    onSelect: (__VLS_ctx.handleSelectSession)
};
const __VLS_8 = {
    onRename: (__VLS_ctx.handleRenameSession)
};
const __VLS_9 = {
    onRemove: (__VLS_ctx.handleRemoveSession)
};
const __VLS_10 = {
    onLogout: (__VLS_ctx.handleLogout)
};
var __VLS_2;
__VLS_asFunctionalElement(__VLS_intrinsicElements.main, __VLS_intrinsicElements.main)({
    ...{ class: "chat-main" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "chat-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "chat-header__left" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.sidebarOpen = !__VLS_ctx.sidebarOpen;
        } },
    ...{ class: "chat-header__menu-btn" },
    title: "切换会话列表",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "chat-header__eyebrow" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
(__VLS_ctx.sessionInfo?.title || '准备开始新的对话');
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "chat-header__subline" },
});
(__VLS_ctx.settings.useRag
    ? __VLS_ctx.selectedDocumentNames.length
        ? `当前检索范围：${__VLS_ctx.selectedDocumentNames.join('、')}`
        : 'RAG 已启用，但当前还没有选中文档。'
    : '当前为普通聊天模式。');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "chat-header__right" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.handleExport) },
    ...{ class: "icon-button" },
    title: "导出对话",
    disabled: (!__VLS_ctx.hasMessages),
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.toggleTheme) },
    ...{ class: "icon-button" },
    title: "切换主题",
});
(__VLS_ctx.theme === 'dark' ? '☀' : '🌙');
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.settingsOpen = !__VLS_ctx.settingsOpen;
        } },
    ...{ class: "chat-header__settings-btn" },
    title: "打开设置",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "chat-header__status" },
    ...{ class: ({ 'chat-header__status--live': __VLS_ctx.isStreaming }) },
});
(__VLS_ctx.isStreaming ? '生成中' : '就绪');
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "chat-stage" },
});
if (__VLS_ctx.hasMessages) {
    /** @type {[typeof MessageList, ]} */ ;
    // @ts-ignore
    const __VLS_11 = __VLS_asFunctionalComponent(MessageList, new MessageList({
        ...{ 'onRetry': {} },
        messages: (__VLS_ctx.messages),
    }));
    const __VLS_12 = __VLS_11({
        ...{ 'onRetry': {} },
        messages: (__VLS_ctx.messages),
    }, ...__VLS_functionalComponentArgsRest(__VLS_11));
    let __VLS_14;
    let __VLS_15;
    let __VLS_16;
    const __VLS_17 = {
        onRetry: (__VLS_ctx.handleRetry)
    };
    var __VLS_13;
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "empty-stage" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
}
if (__VLS_ctx.error) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "error-banner" },
    });
    (__VLS_ctx.error);
}
/** @type {[typeof ComposerBox, ]} */ ;
// @ts-ignore
const __VLS_18 = __VLS_asFunctionalComponent(ComposerBox, new ComposerBox({
    ...{ 'onUpdate': {} },
    ...{ 'onSend': {} },
    ...{ 'onStop': {} },
    value: (__VLS_ctx.draft),
    isStreaming: (__VLS_ctx.isStreaming),
}));
const __VLS_19 = __VLS_18({
    ...{ 'onUpdate': {} },
    ...{ 'onSend': {} },
    ...{ 'onStop': {} },
    value: (__VLS_ctx.draft),
    isStreaming: (__VLS_ctx.isStreaming),
}, ...__VLS_functionalComponentArgsRest(__VLS_18));
let __VLS_21;
let __VLS_22;
let __VLS_23;
const __VLS_24 = {
    onUpdate: (__VLS_ctx.updateDraft)
};
const __VLS_25 = {
    onSend: (__VLS_ctx.handleSend)
};
const __VLS_26 = {
    onStop: (__VLS_ctx.stopStream)
};
var __VLS_20;
/** @type {[typeof SettingsPanel, ]} */ ;
// @ts-ignore
const __VLS_27 = __VLS_asFunctionalComponent(SettingsPanel, new SettingsPanel({
    ...{ 'onUpdate': {} },
    ...{ 'onUpload': {} },
    ...{ 'onRemoveDocument': {} },
    settings: (__VLS_ctx.settings),
    documents: (__VLS_ctx.availableDocuments),
    isUploadingDocuments: (__VLS_ctx.isUploadingDocuments),
    documentError: (__VLS_ctx.documentError),
}));
const __VLS_28 = __VLS_27({
    ...{ 'onUpdate': {} },
    ...{ 'onUpload': {} },
    ...{ 'onRemoveDocument': {} },
    settings: (__VLS_ctx.settings),
    documents: (__VLS_ctx.availableDocuments),
    isUploadingDocuments: (__VLS_ctx.isUploadingDocuments),
    documentError: (__VLS_ctx.documentError),
}, ...__VLS_functionalComponentArgsRest(__VLS_27));
let __VLS_30;
let __VLS_31;
let __VLS_32;
const __VLS_33 = {
    onUpdate: (__VLS_ctx.updateSettings)
};
const __VLS_34 = {
    onUpload: (__VLS_ctx.handleUploadDocuments)
};
const __VLS_35 = {
    onRemoveDocument: (__VLS_ctx.handleRemoveDocument)
};
var __VLS_29;
/** @type {__VLS_StyleScopedClasses['chat-layout']} */ ;
/** @type {__VLS_StyleScopedClasses['overlay']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-main']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header__left']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header__menu-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header__eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header__subline']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header__right']} */ ;
/** @type {__VLS_StyleScopedClasses['icon-button']} */ ;
/** @type {__VLS_StyleScopedClasses['icon-button']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header__settings-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-header__status']} */ ;
/** @type {__VLS_StyleScopedClasses['chat-stage']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-stage']} */ ;
/** @type {__VLS_StyleScopedClasses['error-banner']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            ComposerBox: ComposerBox,
            MessageList: MessageList,
            SessionSidebar: SessionSidebar,
            SettingsPanel: SettingsPanel,
            user: user,
            sessions: sessions,
            currentSessionId: currentSessionId,
            messages: messages,
            hasMessages: hasMessages,
            isStreaming: isStreaming,
            error: error,
            stopStream: stopStream,
            settings: settings,
            availableDocuments: availableDocuments,
            isUploadingDocuments: isUploadingDocuments,
            documentError: documentError,
            updateSettings: updateSettings,
            handleUploadDocuments: handleUploadDocuments,
            draft: draft,
            sessionInfo: sessionInfo,
            sidebarOpen: sidebarOpen,
            settingsOpen: settingsOpen,
            theme: theme,
            toggleTheme: toggleTheme,
            selectedDocumentNames: selectedDocumentNames,
            updateDraft: updateDraft,
            handleCreateSession: handleCreateSession,
            handleSelectSession: handleSelectSession,
            handleRenameSession: handleRenameSession,
            handleSend: handleSend,
            handleRemoveSession: handleRemoveSession,
            handleRemoveDocument: handleRemoveDocument,
            handleRetry: handleRetry,
            handleLogout: handleLogout,
            handleExport: handleExport,
        };
    },
    __typeEmits: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeEmits: {},
});
; /* PartiallyEnd: #4569/main.vue */
