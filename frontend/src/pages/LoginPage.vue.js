import { ref } from 'vue';
import { useAuth } from '../composables/useAuth';
const { login, register, authError, isLoading, isLoggedIn } = useAuth();
const emit = defineEmits();
const mode = ref('login');
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const toggleMode = () => {
    mode.value = mode.value === 'login' ? 'register' : 'login';
    authError.value = null;
};
const handleSubmit = async () => {
    if (!username.value.trim() || !password.value)
        return;
    if (mode.value === 'register' && password.value !== confirmPassword.value) {
        authError.value = '两次密码不一致';
        return;
    }
    let ok;
    if (mode.value === 'login') {
        ok = await login(username.value, password.value);
    }
    else {
        ok = await register(username.value, password.value);
    }
    if (ok) {
        emit('loggedIn');
    }
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['login-card__header']} */ ;
/** @type {__VLS_StyleScopedClasses['login-field']} */ ;
/** @type {__VLS_StyleScopedClasses['login-field']} */ ;
/** @type {__VLS_StyleScopedClasses['login-field']} */ ;
/** @type {__VLS_StyleScopedClasses['login-button']} */ ;
/** @type {__VLS_StyleScopedClasses['login-button']} */ ;
/** @type {__VLS_StyleScopedClasses['login-switch-btn']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "login-page" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "login-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "login-card__header" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "login-card__icon" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "login-card__subtitle" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.form, __VLS_intrinsicElements.form)({
    ...{ onSubmit: (__VLS_ctx.handleSubmit) },
    ...{ class: "login-card__form" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "login-field" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    value: (__VLS_ctx.username),
    type: "text",
    placeholder: "输入用户名",
    autocomplete: "username",
    required: true,
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
    ...{ class: "login-field" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    type: "password",
    placeholder: "输入密码",
    autocomplete: "current-password",
    required: true,
});
(__VLS_ctx.password);
if (__VLS_ctx.mode === 'register') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({
        ...{ class: "login-field" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
        type: "password",
        placeholder: "再次输入密码",
        autocomplete: "new-password",
        required: true,
    });
    (__VLS_ctx.confirmPassword);
}
if (__VLS_ctx.authError) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "login-error" },
    });
    (__VLS_ctx.authError);
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    type: "submit",
    ...{ class: "login-button" },
    disabled: (__VLS_ctx.isLoading),
});
(__VLS_ctx.isLoading ? '请稍候…' : __VLS_ctx.mode === 'login' ? '登录' : '注册');
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "login-card__switch" },
});
(__VLS_ctx.mode === 'login' ? '还没有账号？' : '已有账号？');
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.toggleMode) },
    ...{ class: "login-switch-btn" },
});
(__VLS_ctx.mode === 'login' ? '注册' : '登录');
/** @type {__VLS_StyleScopedClasses['login-page']} */ ;
/** @type {__VLS_StyleScopedClasses['login-card']} */ ;
/** @type {__VLS_StyleScopedClasses['login-card__header']} */ ;
/** @type {__VLS_StyleScopedClasses['login-card__icon']} */ ;
/** @type {__VLS_StyleScopedClasses['login-card__subtitle']} */ ;
/** @type {__VLS_StyleScopedClasses['login-card__form']} */ ;
/** @type {__VLS_StyleScopedClasses['login-field']} */ ;
/** @type {__VLS_StyleScopedClasses['login-field']} */ ;
/** @type {__VLS_StyleScopedClasses['login-field']} */ ;
/** @type {__VLS_StyleScopedClasses['login-error']} */ ;
/** @type {__VLS_StyleScopedClasses['login-button']} */ ;
/** @type {__VLS_StyleScopedClasses['login-card__switch']} */ ;
/** @type {__VLS_StyleScopedClasses['login-switch-btn']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            authError: authError,
            isLoading: isLoading,
            mode: mode,
            username: username,
            password: password,
            confirmPassword: confirmPassword,
            toggleMode: toggleMode,
            handleSubmit: handleSubmit,
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
