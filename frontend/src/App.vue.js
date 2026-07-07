import { ref } from 'vue';
import { useAuth } from './composables/useAuth';
import ChatPage from './pages/ChatPage.vue';
import LoginPage from './pages/LoginPage.vue';
import Toast from './components/Toast.vue';
const { isLoggedIn } = useAuth();
const showChat = ref(isLoggedIn.value);
const handleLoggedIn = () => {
    showChat.value = true;
};
const handleLogout = () => {
    showChat.value = false;
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
if (!__VLS_ctx.showChat) {
    /** @type {[typeof LoginPage, ]} */ ;
    // @ts-ignore
    const __VLS_0 = __VLS_asFunctionalComponent(LoginPage, new LoginPage({
        ...{ 'onLoggedIn': {} },
    }));
    const __VLS_1 = __VLS_0({
        ...{ 'onLoggedIn': {} },
    }, ...__VLS_functionalComponentArgsRest(__VLS_0));
    let __VLS_3;
    let __VLS_4;
    let __VLS_5;
    const __VLS_6 = {
        onLoggedIn: (__VLS_ctx.handleLoggedIn)
    };
    var __VLS_2;
}
else {
    /** @type {[typeof ChatPage, ]} */ ;
    // @ts-ignore
    const __VLS_7 = __VLS_asFunctionalComponent(ChatPage, new ChatPage({
        ...{ 'onLogout': {} },
    }));
    const __VLS_8 = __VLS_7({
        ...{ 'onLogout': {} },
    }, ...__VLS_functionalComponentArgsRest(__VLS_7));
    let __VLS_10;
    let __VLS_11;
    let __VLS_12;
    const __VLS_13 = {
        onLogout: (__VLS_ctx.handleLogout)
    };
    var __VLS_9;
}
/** @type {[typeof Toast, ]} */ ;
// @ts-ignore
const __VLS_14 = __VLS_asFunctionalComponent(Toast, new Toast({}));
const __VLS_15 = __VLS_14({}, ...__VLS_functionalComponentArgsRest(__VLS_14));
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            ChatPage: ChatPage,
            LoginPage: LoginPage,
            Toast: Toast,
            showChat: showChat,
            handleLoggedIn: handleLoggedIn,
            handleLogout: handleLogout,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
