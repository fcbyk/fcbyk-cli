<template>
  <main class="flex gap-5 w-full max-w-[1200px] h-screen px-5 py-8 mx-auto items-center justify-center box-border">
    <div class="flex-1 max-w-[400px] min-w-0">
      <!-- 登录卡片 -->
      <section class="w-full max-w-full p-6 bg-[#1e293b]/90 rounded-[18px] border border-white/5 shadow-[0_20px_60px_rgba(0,0,0,0.25)] backdrop-blur-md box-border">
        <h1 class="m-0 mb-2 text-2xl font-bold text-(--text)">管理员登录</h1>
        <p class="m-0 mb-4 text-sm text-(--muted)">请输入管理员密码以进入管理系统</p>
        <input
          v-model="password"
          type="password"
          placeholder="请输入管理员密码"
          class="w-full p-3 rounded-xl border border-slate-400/60 bg-slate-900/80 text-(--text) text-[15px] outline-hidden focus:border-(--primary) focus:ring-1 focus:ring-(--primary)/40 transition-all"
          @keypress.enter="handleLoginAndRedirect"
        />
        <button 
          class="mt-3 w-full rounded-xl px-4 py-3 text-[15px] font-semibold cursor-pointer transition-all duration-120 active:translate-y-px disabled:opacity-60 disabled:cursor-not-allowed bg-linear-to-br from-(--primary) to-(--accent) shadow-[0_12px_30px_rgba(34,211,238,0.18)] text-[#0b1224]" 
          @click="handleLoginAndRedirect"
        >登录</button>
        <p v-if="loginError" class="text-(--danger) text-[13px] mt-2">{{ loginError }}</p>
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

<style>
body {
  overflow: hidden;
  height: 100vh;
  padding: 0 !important;
}
</style>
