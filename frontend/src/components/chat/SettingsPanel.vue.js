import { ref } from 'vue';
const props = defineProps();
const emit = defineEmits();
const AVAILABLE_MODELS = [
    { value: 'glm-4-flash', label: 'GLM-4-Flash（免费⚡）' },
    { value: 'glm-4-plus', label: 'GLM-4-Plus（强💪）' },
    { value: 'glm-4-air', label: 'GLM-4-Air（轻量🌤）' },
    { value: 'glm-4-long', label: 'GLM-4-Long（长文本📜）' },
];
const isDragOver = ref(false);
const updateField = (key, value) => {
    emit('update', { ...props.settings, [key]: value });
};
const toggleDocument = (documentId, checked) => {
    const nextIds = checked
        ? Array.from(new Set([...props.settings.documentIds, documentId]))
        : props.settings.documentIds.filter((id) => id !== documentId);
    emit('update', { ...props.settings, documentIds: nextIds });
};
const handleModelChange = (event) => {
    updateField('model', event.target.value);
};
const handleTemperatureInput = (event) => {
    updateField('temperature', Number(event.target.value));
};
const handleSystemPromptInput = (event) => {
    updateField('systemPrompt', event.target.value);
};
const handleUseRagChange = (event) => {
    updateField('useRag', event.target.checked);
};
const handleDocumentToggle = (documentId, event) => {
    toggleDocument(documentId, event.target.checked);
};
const handleUpload = (event) => {
    const input = event.target;
    const files = Array.from(input.files ?? []);
    emit('upload', files);
    input.value = '';
};
const handleDragOver = (e) => {
    e.preventDefault();
    isDragOver.value = true;
};
const handleDragLeave = () => {
    isDragOver.value = false;
};
const handleDrop = (e) => {
    e.preventDefault();
    isDragOver.value = false;
    const files = Array.from(e.dataTransfer?.files ?? []);
    if (files.length)
        emit('upload', files);
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "settings-panel" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "panel-title" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "field" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({
    ...{ onChange: (__VLS_ctx.handleModelChange) },
    value: (__VLS_ctx.settings.model),
    ...{ class: "field__select" },
});
for (const [model] of __VLS_getVForSourceType((__VLS_ctx.AVAILABLE_MODELS))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({
        key: (model.value),
        value: (model.value),
    });
    (model.label);
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "field" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
(__VLS_ctx.settings.temperature.toFixed(1));
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onInput: (__VLS_ctx.handleTemperatureInput) },
    type: "range",
    min: "0",
    max: "1.5",
    step: "0.1",
    value: (__VLS_ctx.settings.temperature),
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "field__range-labels" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "field" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.textarea)({
    ...{ onInput: (__VLS_ctx.handleSystemPromptInput) },
    rows: "4",
    value: (__VLS_ctx.settings.systemPrompt),
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "field field--row" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onChange: (__VLS_ctx.handleUseRagChange) },
    type: "checkbox",
    checked: (__VLS_ctx.settings.useRag),
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "field" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onDragover: (__VLS_ctx.handleDragOver) },
    ...{ onDragleave: (__VLS_ctx.handleDragLeave) },
    ...{ onDrop: (__VLS_ctx.handleDrop) },
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.$refs.fileInput?.click();
        } },
    ...{ class: "upload-zone" },
    ...{ class: ({ 'upload-zone--drag': __VLS_ctx.isDragOver, 'upload-zone--disabled': __VLS_ctx.isUploadingDocuments }) },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    ...{ onChange: (__VLS_ctx.handleUpload) },
    ref: "fileInput",
    type: "file",
    accept: ".txt,.md,.pdf,.docx",
    multiple: true,
    hidden: true,
    disabled: (__VLS_ctx.isUploadingDocuments),
});
/** @type {typeof __VLS_ctx.fileInput} */ ;
if (__VLS_ctx.isUploadingDocuments) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "upload-zone__icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
else if (__VLS_ctx.isDragOver) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "upload-zone__icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "upload-zone__icon" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({
        ...{ class: "upload-zone__hint" },
    });
}
if (__VLS_ctx.documentError) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "error-banner settings-error" },
    });
    (__VLS_ctx.documentError);
}
if (__VLS_ctx.documents.length) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "document-list" },
    });
    for (const [document] of __VLS_getVForSourceType((__VLS_ctx.documents))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
            key: (document.id),
            ...{ class: "document-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "document-item__main" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
            ...{ onChange: (...[$event]) => {
                    if (!(__VLS_ctx.documents.length))
                        return;
                    __VLS_ctx.handleDocumentToggle(document.id, $event);
                } },
            type: "checkbox",
            checked: (__VLS_ctx.settings.documentIds.includes(document.id)),
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
        (document.filename);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
        (document.status);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!(__VLS_ctx.documents.length))
                        return;
                    __VLS_ctx.emit('removeDocument', document.id);
                } },
            type: "button",
            ...{ class: "document-item__remove" },
        });
    }
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "empty-panel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
}
/** @type {__VLS_StyleScopedClasses['settings-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-title']} */ ;
/** @type {__VLS_StyleScopedClasses['field']} */ ;
/** @type {__VLS_StyleScopedClasses['field__select']} */ ;
/** @type {__VLS_StyleScopedClasses['field']} */ ;
/** @type {__VLS_StyleScopedClasses['field__range-labels']} */ ;
/** @type {__VLS_StyleScopedClasses['field']} */ ;
/** @type {__VLS_StyleScopedClasses['field']} */ ;
/** @type {__VLS_StyleScopedClasses['field--row']} */ ;
/** @type {__VLS_StyleScopedClasses['field']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-zone']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-zone__icon']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-zone__icon']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-zone__icon']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-zone__hint']} */ ;
/** @type {__VLS_StyleScopedClasses['error-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['settings-error']} */ ;
/** @type {__VLS_StyleScopedClasses['document-list']} */ ;
/** @type {__VLS_StyleScopedClasses['document-item']} */ ;
/** @type {__VLS_StyleScopedClasses['document-item__main']} */ ;
/** @type {__VLS_StyleScopedClasses['document-item__remove']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-panel']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            emit: emit,
            AVAILABLE_MODELS: AVAILABLE_MODELS,
            isDragOver: isDragOver,
            handleModelChange: handleModelChange,
            handleTemperatureInput: handleTemperatureInput,
            handleSystemPromptInput: handleSystemPromptInput,
            handleUseRagChange: handleUseRagChange,
            handleDocumentToggle: handleDocumentToggle,
            handleUpload: handleUpload,
            handleDragOver: handleDragOver,
            handleDragLeave: handleDragLeave,
            handleDrop: handleDrop,
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
