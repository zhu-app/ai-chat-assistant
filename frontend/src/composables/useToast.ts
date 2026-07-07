import { ref } from 'vue';

export interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
}

const toasts = ref<Toast[]>([]);
let nextId = 1;

export const useToast = () => {
  const show = (message: string, type: Toast['type'] = 'info', duration = 2500) => {
    const id = nextId++;
    toasts.value = [...toasts.value, { id, message, type }];
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id);
    }, duration);
  };

  const success = (msg: string) => show(msg, 'success');
  const error = (msg: string) => show(msg, 'error');
  const info = (msg: string) => show(msg, 'info');

  return { toasts, show, success, error, info };
};