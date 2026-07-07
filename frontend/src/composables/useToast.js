import { ref } from 'vue';
const toasts = ref([]);
let nextId = 1;
export const useToast = () => {
    const show = (message, type = 'info', duration = 2500) => {
        const id = nextId++;
        toasts.value = [...toasts.value, { id, message, type }];
        setTimeout(() => {
            toasts.value = toasts.value.filter((t) => t.id !== id);
        }, duration);
    };
    const success = (msg) => show(msg, 'success');
    const error = (msg) => show(msg, 'error');
    const info = (msg) => show(msg, 'info');
    return { toasts, show, success, error, info };
};
