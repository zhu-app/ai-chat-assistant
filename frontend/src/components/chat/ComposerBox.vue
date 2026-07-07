<script setup lang="ts">
const props = defineProps<{
  value: string;
  isStreaming: boolean;
}>();

const emit = defineEmits<{
  update: [value: string];
  send: [];
  stop: [];
}>();

const handleInput = (event: Event) => {
  emit('update', (event.target as HTMLTextAreaElement).value);
};

const onSubmit = () => {
  if (props.isStreaming) {
    emit('stop');
    return;
  }
  emit('send');
};
</script>

<template>
  <section class="composer">
    <textarea
      class="composer__input"
      :value="value"
      rows="4"
      placeholder="发一条消息，开始新的多轮对话。"
      @input="handleInput"
      @keydown.enter.exact.prevent="onSubmit"
    />

    <div class="composer__actions">
      <small>Enter 发送 · Shift + Enter 换行</small>
      <button
        class="primary-button"
        :class="{ 'primary-button--stop': isStreaming }"
        @click="onSubmit"
      >
        {{ isStreaming ? '■ 停止生成' : '发送消息' }}
      </button>
    </div>
  </section>
</template>