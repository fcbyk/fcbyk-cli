<template>
  <main class="admin-layout login-layout">
    <div class="admin-main">
      <!-- 登录卡片 -->
      <section class="card admin-card login-section">
        <h1>管理员登录</h1>
        <p class="desc">请输入管理员密码以进入管理系统</p>
        <input
          v-model="password"
          type="password"
          placeholder="请输入管理员密码"
          @keypress.enter="handleLoginAndRedirect"
        />
        <button class="primary" style="margin-top: 12px; width: 100%" @click="handleLoginAndRedirect">登录</button>
        <p v-if="loginError" class="error-msg">{{ loginError }}</p>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAdmin } from './composables/useAdmin'

const router = useRouter()
const {
  password,
  loginError,
  handleLogin
} = useAdmin()

async function handleLoginAndRedirect() {
  await handleLogin()
  if (sessionStorage.getItem('admin_authed') === '1') {
    router.push('/admin')
  }
}
</script>

<style scoped lang="scss">
@use './style.scss' as *;

:global(body) {
  overflow: hidden;
  height: 100vh;
  padding: 0 !important;
}

.admin-layout {
  display: flex;
  gap: 20px;
  width: 100%;
  max-width: 1200px;
  height: 100vh;
  padding: 32px 20px;
  margin: 0 auto;
  align-items: flex-start;
  box-sizing: border-box;
}

.login-layout {
  justify-content: center;
  align-items: center;
}

.admin-main {
  flex: 1;
  max-width: 400px;
  min-width: 0;
}

.admin-card {
  width: 100%;
  box-sizing: border-box;
  @include card(100%, 24px, rgba(30, 41, 59, 0.9));
}

h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.desc {
  margin: 0 0 16px;
  color: var(--muted);
  font-size: 14px;
}

button {
  @include button-base;
  &.primary {
    @include button-primary;
  }
  &:disabled {
    @include button-disabled;
  }
  &:not(:disabled):active {
    @include button-active;
  }
}

.login-section {
  width: 100%;
  margin: auto;
  input {
    width: 100%;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.6);
    background: rgba(15, 23, 42, 0.8);
    color: var(--text);
    font-size: 15px;
    outline: none;
    &:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.4);
    }
  }
}

.error-msg {
  color: var(--danger);
  font-size: 13px;
  margin-top: 8px;
}
</style>
