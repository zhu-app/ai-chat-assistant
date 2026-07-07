import { computed, nextTick, ref, watch } from 'vue';
import { Marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
// highlight.js 按需加载（较大，避免首屏加载）
let marked = null;
async function getMarked() {
    if (marked)
        return marked;
    const hljs = await import('highlight.js');
    marked = new Marked(markedHighlight({
        langPrefix: 'hljs language-',
        highlight(code, lang) {
            if (lang && hljs.default.getLanguage(lang)) {
                try {
                    return hljs.default.highlight(code, { language: lang }).value;
                }
                catch { /* fallthrough */ }
            }
            return hljs.default.highlightAuto(code).value;
        },
    }), { gfm: true, breaks: true });
    return marked;
}
const props = defineProps();
const emit = defineEmits();
const listRef = ref(null);
const copiedMessageId = ref(null);
const assistantEntries = computed(() => props.messages.filter((message) => message.role === 'assistant'));
const scrollToBottom = async () => {
    await nextTick();
    const container = listRef.value;
    if (!container)
        return;
    container.scrollTop = container.scrollHeight;
};
const renderMessageContent = (content) => {
    // 同步时：清空占位，由 mounted 钩子异步渲染
    const placeholderId = `__md_${Math.random().toString(36).slice(2, 8)}`;
    return `<span data-md-placeholder="${placeholderId}">${escapeHtml(content)}</span>`;
};
// 真正的 Markdown 渲染，异步执行
const renderMarkdownAsync = async () => {
    const md = await getMarked();
    document.querySelectorAll('[data-md-placeholder]').forEach((el) => {
        const content = el.textContent || '';
        try {
            const html = md.parse(content);
            el.outerHTML = typeof html === 'string' ? html : escapeHtml(content);
        }
        catch {
            el.outerHTML = escapeHtml(content);
        }
    });
};
// 消息更新后触发异步渲染
watch(() => props.messages.map((m) => `${m.id}:${m.content.length}:${m.status}`).join('|'), () => {
    scrollToBottom();
    // 等 DOM 更新后异步渲染 Markdown
    nextTick(() => renderMarkdownAsync());
}, { immediate: true });
// 简单的 HTML 转义（用于同步占位）
const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};
const copyMessage = async (message) => {
    if (!message.content)
        return;
    await navigator.clipboard.writeText(message.content);
    copiedMessageId.value = message.id;
    window.setTimeout(() => {
        if (copiedMessageId.value === message.id)
            copiedMessageId.value = null;
    }, 1200);
};
const canRetry = (messageIndex) => {
    for (let index = messageIndex - 1; index >= 0; index -= 1) {
        if (props.messages[index]?.role === 'user')
            return true;
    }
    return false;
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ref: "listRef",
    ...{ class: "message-list" },
});
/** @type {typeof __VLS_ctx.listRef} */ ;
for (const [message, index] of __VLS_getVForSourceType((__VLS_ctx.messages))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
        key: (message.id),
        ...{ class: "message-item" },
        ...{ class: (`message-item--${message.role}`) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "message-item__avatar" },
    });
    (message.role === 'user' ? '我' : 'AI');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "message-item__body" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "message-item__label" },
    });
    (message.role === 'user' ? '你' : 'AI');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "message-item__bubble" },
    });
    if (message.content) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div)({
            ...{ class: "message-item__content" },
        });
        __VLS_asFunctionalDirective(__VLS_directives.vHtml)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.renderMessageContent(message.content)) }, null, null);
    }
    else if (message.status === 'streaming') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    }
    else if (message.status === 'aborted') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "message-item__aborted" },
        });
    }
    if (message.sources?.length) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "message-item__sources" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "message-item__sources-title" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "message-item__source-list" },
        });
        for (const [source] of __VLS_getVForSourceType((message.sources))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                key: (`${message.id}-${source.documentId}-${source.chunkIndex ?? 0}`),
                ...{ class: "message-source-card" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "message-source-card__main" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
            (source.filename);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            ((source.chunkIndex ?? 0) + 1);
            (Number(source.score ?? 0).toFixed(0));
            if (source.preview) {
                __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
                    ...{ class: "message-source-card__preview" },
                });
                (source.preview);
            }
        }
    }
    if (message.role === 'assistant') {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "message-item__actions" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(message.role === 'assistant'))
                        return;
                    __VLS_ctx.copyMessage(message);
                } },
            type: "button",
            ...{ class: "message-action" },
        });
        (__VLS_ctx.copiedMessageId === message.id ? '已复制' : '复制');
        if (__VLS_ctx.canRetry(index)) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!(message.role === 'assistant'))
                            return;
                        if (!(__VLS_ctx.canRetry(index)))
                            return;
                        __VLS_ctx.emit('retry', message.id);
                    } },
                type: "button",
                ...{ class: "message-action" },
            });
        }
    }
}
if (__VLS_ctx.assistantEntries.length >= 2) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "message-list__hint" },
    });
}
/** @type {__VLS_StyleScopedClasses['message-list']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__body']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__label']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__bubble']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__content']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__aborted']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__sources']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__sources-title']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__source-list']} */ ;
/** @type {__VLS_StyleScopedClasses['message-source-card']} */ ;
/** @type {__VLS_StyleScopedClasses['message-source-card__main']} */ ;
/** @type {__VLS_StyleScopedClasses['message-source-card__preview']} */ ;
/** @type {__VLS_StyleScopedClasses['message-item__actions']} */ ;
/** @type {__VLS_StyleScopedClasses['message-action']} */ ;
/** @type {__VLS_StyleScopedClasses['message-action']} */ ;
/** @type {__VLS_StyleScopedClasses['message-list__hint']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            emit: emit,
            listRef: listRef,
            copiedMessageId: copiedMessageId,
            assistantEntries: assistantEntries,
            renderMessageContent: renderMessageContent,
            copyMessage: copyMessage,
            canRetry: canRetry,
        };
    },
    __typeEmits: {},
    __typeProps: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeEmits: {},
    __typeProps: {},
});
; /* PartiallyEnd: #4569/main.vue */
