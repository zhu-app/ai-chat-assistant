<script setup lang="ts">
import ChatPage from './pages/ChatPage.vue';
import SharedChatPage from './pages/SharedChatPage.vue';
import Toast from './components/Toast.vue';

const sharedToken = (() => {
  const match = window.location.pathname.match(/^\/share\/([^/]+)\/?$/);
  return match?.[1] ?? null;
})();
</script>

<template>
  <SharedChatPage v-if="sharedToken" :token="sharedToken" />
  <template v-else>
    <ChatPage />
    <Toast />
  </template>
</template>
