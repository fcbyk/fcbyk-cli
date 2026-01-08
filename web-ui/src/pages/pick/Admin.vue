<template>
  <main class="card admin-card">
    <h1>兑换码管理</h1>
    <p class="desc">管理员查看与分发抽奖码</p>

    <!-- 登录 -->
    <div v-if="!isAuthenticated" class="login-section">
      <input
        v-model="password"
        type="password"
        placeholder="请输入管理员密码"
        @keypress.enter="handleLogin"
      />
      <button class="primary" style="margin-top: 12px" @click="handleLogin">登录</button>
      <p v-if="loginError" class="error-msg">{{ loginError }}</p>
    </div>

    <!-- 面板 -->
    <div v-else class="panel">
      <!-- 统计条 -->
      <div class="stats">
        <div class="stat">
          <div class="label">总数</div>
          <div class="value">{{ stats.total }}</div>
        </div>
        <div class="stat">
          <div class="label">已使用</div>
          <div class="value used">{{ stats.used }}</div>
        </div>
        <div class="stat">
          <div class="label">剩余</div>
          <div class="value left">{{ stats.left }}</div>
        </div>
      </div>

      <!-- 新增兑换码 + 快捷操作 -->
      <div class="add-code-section">
        <div class="add-code-form">
          <input
            v-model="newCode"
            type="text"
            placeholder="请输入兑换码"
            maxlength="20"
            @keypress.enter="handleAddCode"
          />
          <button class="primary" @click="handleAddCode">新增</button>
          <button class="primary" @click="handleGenCodes">批量生成(5)</button>
          <button class="secondary" @click="handleExportCodes">导出</button>
          <button class="danger" @click="handleClearCodes">清空</button>
        </div>

        <div class="add-code-msgs">
          <div :class="['add-code-msg', addCodeMsgType]">{{ addCodeMsg }}</div>
          <div :class="['msg', genMsgType]">{{ genMsg }}</div>
          <div :class="['msg', exportMsgType]">{{ exportMsg }}</div>
          <div :class="['msg', clearMsgType]">{{ clearMsg }}</div>
        </div>
      </div>

      <!-- 列表 -->
      <div class="table">
        <div class="row" v-for="codeInfo in codes" :key="codeInfo.code">
          <div :class="['code', { used: codeInfo.used }]">
            <span v-if="codeInfo.used || isCodeRevealed(codeInfo.code)" class="hidden">
              {{ codeInfo.code }}
            </span>
            <span v-else class="hidden">
              {{ maskCode(codeInfo.code) }}
            </span>
          </div>

          <div :class="['status', codeInfo.used ? 'bad' : 'ok']">
            {{ codeInfo.used ? '已使用' : '未使用' }}
          </div>

          <div class="actions">
            <button
              v-if="!codeInfo.used"
              class="secondary small"
              @click="toggleReveal(codeInfo.code)"
            >
              {{ isCodeRevealed(codeInfo.code) ? '隐藏' : '查看' }}
            </button>
            <button class="primary small" @click="copyCode(codeInfo.code)">
              {{ isCodeCopied(codeInfo.code) ? '已复制' : '复制' }}
            </button>
            <button
              v-if="codeInfo.used"
              class="secondary small"
              @click="handleResetCode(codeInfo.code)"
            >
              重置
            </button>
            <button class="danger small" @click="handleDeleteCode(codeInfo.code)">删除</button>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useAdmin } from './composables/useAdmin'

const {
  password,
  loginError,
  isAuthenticated,
  codes,
  newCode,
  addCodeMsg,
  addCodeMsgType,
  stats,
  genMsg,
  genMsgType,
  clearMsg,
  clearMsgType,
  exportMsg,
  exportMsgType,
  maskCode,
  handleLogin,
  toggleReveal,
  copyCode,
  handleAddCode,
  handleGenCodes,
  handleDeleteCode,
  handleResetCode,
  handleClearCodes,
  handleExportCodes,
  isCodeRevealed,
  isCodeCopied,
  init,
  _stopPolling
} = useAdmin()

// 初始化（自动恢复登录状态）
onMounted(() => {
  init()
})

// 页面卸载时停止轮询，避免后台持续请求
onUnmounted(() => {
  _stopPolling()
})
</script>

<style scoped>
.admin-card {
  width: min(720px, 100%);
  background: rgba(30, 41, 59, 0.9);
  padding: 24px;
}

h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

/* ===== 登录 ===== */
.login-section input {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.6);
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  font-size: 15px;
  outline: none;
}

.login-section input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.4);
}

.error-msg {
  color: var(--danger);
  font-size: 13px;
  margin-top: 8px;
}

button.small {
  padding: 8px 14px;
  font-size: 13px;
}

button:active {
  transform: translateY(1px);
}

/* ===== 统计条 ===== */
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.stat {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 12px 14px;
  text-align: center;
}

.stat .label {
  font-size: 12px;
  color: var(--muted);
}

.stat .value {
  font-size: 22px;
  font-weight: 800;
  margin-top: 4px;
}

.stat .value.used {
  color: var(--accent);
}

.stat .value.left {
  color: var(--primary);
}

/* ===== 列表 ===== */
.table {
  margin-top: 8px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.row:last-child {
  border-bottom: none;
}

.code {
  font-size: 15px;
}

.hidden {
  background: rgba(255, 255, 255, 0.14);
  border-radius: 8px;
  padding: 6px 12px;
}

.code.used {
  color: var(--muted);
}

.status {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
}

.status.ok {
  color: var(--success);
}

.status.bad {
  color: var(--danger);
}

.actions {
  display: flex;
  gap: 8px;
  white-space: nowrap;
}

/* ===== 新增兑换码 + 快捷操作 ===== */
.add-code-section {
  margin-bottom: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
}

.add-code-form {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.add-code-form input {
  flex: 1;
  min-width: 220px;
  margin: 0;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.6);
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  font-size: 15px;
  outline: none;
}

.add-code-form input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.4);
}

.add-code-form button {
  white-space: nowrap;
}

.add-code-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

button.danger {
  background: rgba(239, 68, 68, 0.9);
  border: 1px solid rgba(239, 68, 68, 0.6);
  color: white;
}

.add-code-msgs {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.add-code-msg {
  font-size: 13px;
  min-height: 18px;
}

.add-code-msg.success {
  color: var(--success);
}

.add-code-msg.error {
  color: var(--danger);
}

.msg {
  font-size: 12px;
  min-height: 16px;
  color: var(--muted);
}

.msg.success {
  color: var(--success);
}

.msg.error {
  color: var(--danger);
}

/* ===== 响应式 ===== */
@media (max-width: 640px) {
  .row {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "code status"
      "actions actions";
  }

  .code {
    grid-area: code;
  }

  .status {
    grid-area: status;
    justify-self: end;
  }

  .actions {
    grid-area: actions;
    justify-content: flex-end;
    margin-top: 6px;
    flex-wrap: wrap;
  }

  .add-code-form input {
    min-width: 100%;
  }

  .add-code-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
