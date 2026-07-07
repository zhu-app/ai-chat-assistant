import { computed, ref } from 'vue';
const props = defineProps();
const emit = defineEmits();
const searchQuery = ref('');
const hasSessions = computed(() => props.sessions.length > 0);
const filteredSessions = computed(() => {
    if (!searchQuery.value.trim())
        return props.sessions;
    const q = searchQuery.value.toLowerCase();
    return props.sessions.filter((s) => s.title.toLowerCase().includes(q));
});
const editingId = ref(null);
const editTitle = ref('');
const startRename = (sessionId, currentTitle) => {
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
const formatTime = (iso) => {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1)
        return '刚刚';
    if (diffMin < 60)
        return `${diffMin} 分钟前`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24)
        return `${diffHour} 小时前`;
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
    ...{ class: "sidebar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "sidebar__header" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "sidebar__eyebrow" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "sidebar__header-actions" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.emit('close');
        } },
    ...{ class: "ghost-button sidebar__close-btn" },
    title: "关闭侧栏",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.emit('create');
        } },
    ...{ class: "ghost-button" },
});
if (__VLS_ctx.hasSessions) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sidebar__search" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        value: (__VLS_ctx.searchQuery),
        ...{ class: "sidebar__search-input" },
        type: "text",
        placeholder: "搜索对话…",
    });
}
if (__VLS_ctx.hasSessions) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "session-list" },
    });
    for (const [session] of __VLS_getVForSourceType((__VLS_ctx.filteredSessions))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.hasSessions))
                        return;
                    __VLS_ctx.emit('select', session.id);
                } },
            key: (session.id),
            ...{ class: "session-card" },
            ...{ class: ({ 'session-card--active': session.id === __VLS_ctx.currentSessionId }) },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "session-card__main" },
        });
        if (__VLS_ctx.editingId === session.id) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
                ...{ onClick: () => { } },
                ...{ onKeydown: (__VLS_ctx.saveRename) },
                ...{ onKeydown: (__VLS_ctx.cancelRename) },
                ...{ onBlur: (__VLS_ctx.saveRename) },
                ...{ class: "session-card__edit-input" },
                ref: "editInput",
                autofocus: true,
            });
            (__VLS_ctx.editTitle);
            /** @type {typeof __VLS_ctx.editInput} */ ;
        }
        else {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
            (session.title);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (session.model);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "session-card__meta" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "session-card__time" },
        });
        (__VLS_ctx.formatTime(session.updatedAt));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "session-card__actions" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.hasSessions))
                        return;
                    __VLS_ctx.startRename(session.id, session.title);
                } },
            ...{ class: "session-card__action" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.hasSessions))
                        return;
                    __VLS_ctx.emit('remove', session.id);
                } },
            ...{ class: "session-card__action session-card__action--danger" },
        });
    }
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "empty-panel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
}
if (__VLS_ctx.user) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sidebar__user" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "sidebar__user-avatar" },
    });
    (__VLS_ctx.user.username.charAt(0).toUpperCase());
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "sidebar__user-name" },
    });
    (__VLS_ctx.user.username);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!(__VLS_ctx.user))
                    return;
                __VLS_ctx.emit('logout');
            } },
        ...{ class: "sidebar__user-logout" },
        title: "退出登录",
    });
}
/** @type {__VLS_StyleScopedClasses['sidebar']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__header']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__header-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['ghost-button']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__close-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['ghost-button']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__search']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__search-input']} */ ;
/** @type {__VLS_StyleScopedClasses['session-list']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__main']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__edit-input']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__meta']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__time']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__actions']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__action']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__action']} */ ;
/** @type {__VLS_StyleScopedClasses['session-card__action--danger']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__user']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__user-avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__user-name']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar__user-logout']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            emit: emit,
            searchQuery: searchQuery,
            hasSessions: hasSessions,
            filteredSessions: filteredSessions,
            editingId: editingId,
            editTitle: editTitle,
            startRename: startRename,
            saveRename: saveRename,
            cancelRename: cancelRename,
            formatTime: formatTime,
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
