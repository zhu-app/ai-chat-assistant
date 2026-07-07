const props = defineProps();
const emit = defineEmits();
const handleInput = (event) => {
    emit('update', event.target.value);
};
const onSubmit = () => {
    if (props.isStreaming) {
        emit('stop');
        return;
    }
    emit('send');
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "composer" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.textarea)({
    ...{ onInput: (__VLS_ctx.handleInput) },
    ...{ onKeydown: (__VLS_ctx.onSubmit) },
    ...{ class: "composer__input" },
    value: (__VLS_ctx.value),
    rows: "4",
    placeholder: "发一条消息，开始新的多轮对话。",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "composer__actions" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.onSubmit) },
    ...{ class: "primary-button" },
    ...{ class: ({ 'primary-button--stop': __VLS_ctx.isStreaming }) },
});
(__VLS_ctx.isStreaming ? '■ 停止生成' : '发送消息');
/** @type {__VLS_StyleScopedClasses['composer']} */ ;
/** @type {__VLS_StyleScopedClasses['composer__input']} */ ;
/** @type {__VLS_StyleScopedClasses['composer__actions']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-button']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            handleInput: handleInput,
            onSubmit: onSubmit,
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
