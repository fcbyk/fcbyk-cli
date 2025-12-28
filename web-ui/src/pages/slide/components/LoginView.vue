<template>
    <div class="login-container">
      <div class="login-box">
        <div class="login-title">PPT 遥控器</div>
        <input
          ref="passwordInputRef"
          v-model="password"
          type="password"
          class="login-input"
          placeholder="请输入访问密码"
          autocomplete="off"
          @keypress.enter="handleLogin"
        />
        <button class="login-btn" :disabled="isLoading" @click="handleLogin">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
        <div class="error-message">{{ errorMessage }}</div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted } from 'vue'
  
  interface Props {
    isLoading?: boolean
    errorMessage?: string
  }
  
  interface Emits {
    (e: 'login', password: string): void
  }
  
  const props = withDefaults(defineProps<Props>(), {
    isLoading: false,
    errorMessage: ''
  })
  
  const emit = defineEmits<Emits>()
  
  const password = ref('')
  const passwordInputRef = ref<HTMLInputElement | null>(null)
  
  function handleLogin() {
    emit('login', password.value)
  }
  
  // 自动聚焦输入框
  onMounted(() => {
    passwordInputRef.value?.focus()
  })
  </script>