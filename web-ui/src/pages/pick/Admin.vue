<template>
  <main class="admin-layout">
    <!-- 移动端标题栏 -->
    <header class="mobile-header">
      <button class="mobile-menu-btn" @click="isSidebarOpen = true">
        <span class="icon">☰</span>
      </button>
      <h1 class="mobile-title">管理后台</h1>
      <div class="mobile-header-right"></div>
    </header>

    <!-- 侧边栏遮罩层 -->
    <div 
      v-if="isSidebarOpen" 
      class="sidebar-overlay" 
      @click="isSidebarOpen = false"
    ></div>

    <!-- 侧边栏 -->
    <aside :class="['card', 'admin-sidebar', { open: isSidebarOpen }]">
      <div class="sidebar-header">
        <h2>管理后台</h2>
        <button class="close-sidebar" @click="isSidebarOpen = false">×</button>
      </div>
      <nav class="sidebar-nav">
        <button
          :class="['nav-item', { active: activeTab === 'codes' }]"
          @click="selectTab('codes')"
        >
          <span class="icon">🎟️</span>
          抽奖码管理
        </button>
        <button
          :class="['nav-item', { active: activeTab === 'free' }]"
          @click="selectTab('free')"
        >
          <span class="icon">🎲</span>
          自由抽奖
        </button>
        <button class="logout-btn" @click="handleLogout">
          退出登录
        </button>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <div class="admin-main">
      <!-- 抽奖码管理面板 -->
      <section v-if="activeTab === 'codes'" class="card admin-card">
        <div class="panel">
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
      </section>

      <!-- 自由抽奖管理面板 -->
      <section v-else-if="activeTab === 'free'" class="card admin-card">
        <h1>自由抽奖</h1>
        <p class="desc">配置和管理自由抽奖活动</p>
        
        <div class="placeholder-content">
          <div class="empty-state">
            <span class="empty-icon">🏗️</span>
            <p>自由抽奖管理功能正在开发中...</p>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAdmin } from './composables/useAdmin'

const router = useRouter()
const activeTab = ref<'codes' | 'free'>('codes')
const isSidebarOpen = ref(false)

function selectTab(tab: 'codes' | 'free') {
  activeTab.value = tab
  isSidebarOpen.value = false
}

const {
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

// 退出登录
function handleLogout() {
  sessionStorage.removeItem('admin_authed')
  sessionStorage.removeItem('admin_pw')
  _stopPolling()
  router.push('/admin/login')
}

// 页面卸载时停止轮询，避免后台持续请求
onUnmounted(() => {
  _stopPolling()
})
</script>

<style scoped>
:global(body) {
  overflow: hidden;
  height: 100vh;
  padding: 0 !important;
  margin: 0;
}

:global(#app) {
  width: 100%;
  height: 100%;
  display: block;
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

.admin-sidebar {
  width: 240px;
  height: 100%;
  flex-shrink: 0;
  background: rgba(30, 41, 59, 0.9);
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.mobile-menu-btn {
  display: none;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: transparent;
  border: none;
  color: var(--text);
  font-size: 20px;
  cursor: pointer;
  align-items: center;
  justify-content: center;
}

.mobile-header {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 56px;
  background: rgba(30, 41, 59, 0.9);
  backdrop-filter: blur(8px);
  z-index: 990;
  padding: 0 12px;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  box-sizing: border-box;
}

.mobile-title {
  font-size: 17px;
  font-weight: 600;
  margin: 0;
  color: var(--text);
  letter-spacing: 0.5px;
}

.mobile-header-right {
  width: 40px; /* 占位以保持标题居中 */
}

.sidebar-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 998;
}

.close-sidebar {
  display: none;
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
}

.sidebar-header {
  padding: 0 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-header h2 {
  font-size: 18px;
  margin: 0;
  color: var(--primary);
  letter-spacing: 1px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 10px;
  flex: 1;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.sidebar-nav::-webkit-scrollbar {
  display: none;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: var(--text);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 15px;
  text-align: left;
  width: 100%;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.nav-item.active {
  background: rgba(34, 211, 238, 0.15);
  color: var(--primary);
  font-weight: 600;
}

.nav-item .icon {
  font-size: 18px;
}

.admin-main {
  flex: 1;
  height: 100%;
  min-width: 0;
  overflow: hidden;
}

.admin-card {
  width: 100%;
  height: 100%;
  background: rgba(30, 41, 59, 0.9);
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.panel {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.panel::-webkit-scrollbar {
  display: none; /* Chrome, Safari and Opera */
}

h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

/* ===== 统计条 ===== */
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.logout-btn {
  margin-top: auto;
  color: var(--danger);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0;
  padding-top: 16px;
  gap: 12px;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 15px;
  text-align: left;
  width: 100%;
}

.logout-btn:hover {
  color: var(--danger);
}

button.small {
  padding: 8px 14px;
  font-size: 13px;
}

button:active {
  transform: translateY(1px);
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

/* ===== 自由抽奖占位 ===== */
.placeholder-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.placeholder-content::-webkit-scrollbar {
  display: none;
}

.empty-state {
  text-align: center;
  color: var(--muted);
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

/* ===== 响应式 ===== */
@media (max-width: 860px) {
  .admin-layout {
    padding: 56px 0 0;
    height: 100vh;
    gap: 0;
    overflow-x: hidden;
    flex-direction: column;
    width: 100%;
    max-width: none;
    align-items: stretch;
  }

  .mobile-header {
    display: flex;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .sidebar-overlay {
    display: block;
  }

  .admin-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
    width: 260px;
    height: 100vh;
    border-radius: 0 20px 20px 0;
    transform: translateX(-100%);
    box-shadow: none;
    visibility: hidden;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), visibility 0.3s;
  }

  .admin-sidebar.open {
    transform: translateX(0);
    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.4);
    visibility: visible;
  }

  .close-sidebar {
    display: block;
  }

  .sidebar-header {
    display: flex;
  }

  .sidebar-nav {
    flex-direction: column;
    overflow-y: auto;
    padding: 0 10px;
  }

  .nav-item {
    width: 100%;
    white-space: normal;
  }

  /* 管理界面在移动端占满全屏并移除边框 */
  .admin-card {
    border-radius: 0;
    border: none;
    background: rgba(30, 41, 59, 0.9);
    padding: 16px;
    flex: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    max-width: none;
  }

  .admin-main {
    padding: 0;
    display: flex;
    flex-direction: column;
    flex: 1;
    height: auto;
    min-height: 0;
  }

  /* 统计条在移动端压缩空间 */
  .stats {
    gap: 8px;
  }

  .stat {
    padding: 8px 4px;
    border-radius: 10px;
  }

  .stat .value {
    font-size: 18px;
  }

  /* 新增兑换码表单在移动端更紧凑 */
  .add-code-section {
    padding: 12px;
  }

  .add-code-form {
    gap: 6px;
  }

  .add-code-form button {
    flex: 1;
    padding: 10px 8px;
    font-size: 13px;
    min-width: calc(50% - 6px); /* 每行两个按钮 */
  }

  .placeholder-content {
    padding: 20px 12px;
  }

  h1 {
    font-size: 20px;
    margin-bottom: 4px;
  }

  p.desc {
    font-size: 13px;
    margin-bottom: 12px;
  }
}

@media (max-width: 640px) {
  .row {
    grid-template-columns: 1fr auto;
    grid-template-areas:
      "code status"
      "actions actions";
  }

  .code {
    grid-area: code;
    font-size: 17px;
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
    gap: 4px;
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
