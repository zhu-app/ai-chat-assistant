<script setup lang="ts">
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
</script>

<template>
  <LoginPage v-if="!showChat" @logged-in="handleLoggedIn" />
  <ChatPage v-else @logout="handleLogout" />
  <Toast />
</template>