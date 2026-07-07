<script setup lang="ts">
import { useToast } from '../composables/useToast';

const { toasts } = useToast();
</script>

<template>
  <div class="toast-container">
    <transition-group name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast-item"
        :class="`toast-item--${toast.type}`"
      >
        <span class="toast-icon">
          {{ toast.type === 'success' ? '✓' : toast.type === 'error' ? '✕' : 'ℹ' }}
        </span>
        {{ toast.message }}
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  pointer-events: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(12px);
  max-width: 360px;
}

.toast-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.toast-item--success {
  background: rgba(62, 191, 111, 0.15);
  border: 1px solid rgba(62, 191, 111, 0.3);
  color: #3ebb6f;
}
.toast-item--success .toast-icon {
  background: rgba(62, 191, 111, 0.2);
}

.toast-item--error {
  background: rgba(242, 90, 90, 0.15);
  border: 1px solid rgba(242, 90, 90, 0.3);
  color: #f25a5a;
}
.toast-item--error .toast-icon {
  background: rgba(242, 90, 90, 0.2);
}

.toast-item--info {
  background: rgba(79, 124, 255, 0.15);
  border: 1px solid rgba(79, 124, 255, 0.3);
  color: #7da1ff;
}
.toast-item--info .toast-icon {
  background: rgba(79, 124, 255, 0.2);
}

.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
