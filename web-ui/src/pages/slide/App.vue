<template>
  <div>
    <!-- 登录界面 -->
    <LoginView
      v-if="!isAuthenticated"
      :is-loading="isLoading"
      :error-message="errorMessage"
      @login="handleLogin"
    />

    <!-- 触摸板界面 -->
    <TouchpadView v-else />
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import LoginView from './components/LoginView.vue'
import TouchpadView from './components/TouchpadView.vue'
import { useAuth } from './composables/useAuth'
import { useViewport } from './composables/useViewport'
import { initSocket } from './socket'

// 修复移动端视口高度
useViewport()

// 认证逻辑
const { isAuthenticated, isLoading, errorMessage, login } = useAuth()

// 登录处理
async function handleLogin(password: string) {
  const success = await login(password)
  if (success) {
    // 登录成功，初始化 WebSocket
    initSocket()
  }
}

// 监听认证状态变化
watch(isAuthenticated, (authenticated) => {
  if (authenticated) {
    // 已认证，初始化 WebSocket
    initSocket()
  }
})
</script>