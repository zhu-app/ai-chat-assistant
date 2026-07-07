import { computed, ref } from 'vue';
import { listMessages, streamChat } from '../services/chat';
import { uid } from '../utils/id';
export const useMessages = () => {
    const messages = ref([]);
    const isStreaming = ref(false);
    const error = ref(null);
    const controller = ref(null);
    const hasMessages = computed(() => messages.value.length > 0);
    const loadMessages = async (sessionId) => {
        if (!sessionId) {
            messages.value = [];
            return;
        }
        messages.value = await listMessages(sessionId);
    };
    const stopStream = () => {
        controller.value?.abort();
        controller.value = null;
        isStreaming.value = false;
        // 将正在 streaming 的消息标记为 aborted
        const streamingMsg = messages.value.find((item) => item.role === 'assistant' && item.status === 'streaming');
        if (streamingMsg) {
            streamingMsg.status = 'aborted';
            messages.value = [...messages.value];
        }
    };
    const ensureAssistantMessage = (sessionId, messageId) => {
        const existing = messages.value.find((item) => item.id === messageId);
        if (existing)
            return existing;
        const created = {
            id: messageId,
            sessionId,
            role: 'assistant',
            content: '',
            status: 'streaming',
            createdAt: new Date().toISOString(),
        };
        messages.value = [...messages.value, created];
        return created;
    };
    const applyEvent = (event, onSessionCreated) => {
        if (event.type === 'session_created' && event.sessionId) {
            onSessionCreated(event.sessionId, String(event.meta?.title ?? '新对话'));
            return;
        }
        if (event.type === 'message_started' && event.sessionId && event.messageId) {
            ensureAssistantMessage(event.sessionId, event.messageId);
            return;
        }
        if (event.type === 'token' && event.sessionId && event.messageId) {
            const target = ensureAssistantMessage(event.sessionId, event.messageId);
            target.content += event.delta ?? '';
            target.status = 'streaming';
            messages.value = [...messages.value];
            return;
        }
        if (event.type === 'message_done' && event.messageId) {
            const target = messages.value.find((item) => item.id === event.messageId);
            if (target) {
                // 如果消息已被前端标记为 aborted（用户手动停止），不再覆盖状态
                if (target.status === 'aborted') {
                    messages.value = [...messages.value];
                    isStreaming.value = false;
                    controller.value = null;
                    return;
                }
                target.status = 'done';
                if (typeof event.meta?.content === 'string') {
                    target.content = event.meta.content;
                }
                if (Array.isArray(event.meta?.sources)) {
                    target.sources = event.meta.sources;
                }
                messages.value = [...messages.value];
            }
            isStreaming.value = false;
            controller.value = null;
            return;
        }
        if (event.type === 'error') {
            error.value = String(event.meta?.message ?? '生成失败');
            isStreaming.value = false;
            controller.value = null;
        }
    };
    const sendMessage = async (payload, onSessionCreated) => {
        error.value = null;
        isStreaming.value = true;
        controller.value = new AbortController();
        const provisionalSessionId = payload.sessionId ?? 'pending-session';
        messages.value = [
            ...messages.value,
            {
                id: uid(),
                sessionId: provisionalSessionId,
                role: 'user',
                content: payload.message,
                status: 'done',
                createdAt: new Date().toISOString(),
            },
        ];
        try {
            await streamChat(payload, {
                signal: controller.value.signal,
                onEvent: (event) => applyEvent(event, onSessionCreated),
            });
        }
        catch (err) {
            if (err.name === 'AbortError') {
                isStreaming.value = false;
                controller.value = null;
                return;
            }
            error.value = err instanceof Error ? err.message : '请求失败';
            isStreaming.value = false;
            controller.value = null;
        }
    };
    return {
        messages,
        hasMessages,
        isStreaming,
        error,
        loadMessages,
        sendMessage,
        stopStream,
    };
};
