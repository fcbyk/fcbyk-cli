<template>
  <div class="control-interface">
    <!-- Header -->
    <header class="header">
      <div 
        class="status-indicator" 
        :class="{ 'connected': isSocketConnected, 'connecting': isConnecting }"
        @click="handleReconnect"
      >
        <div class="dot"></div>
        <span class="status-text">{{ statusText }}</span>
        <span v-if="isSocketConnected" class="latency-text">{{ latency }}ms</span>
      </div>
      <div class="header-actions">
        <button class="icon-btn" @click="toggleDarkMode">
          <component :is="isDark ? Moon : Sun" class="icon" />
        </button>
        <div class="settings-menu-container" v-click-outside="closeSettings">
          <button class="icon-btn" @click.stop="toggleSettings" @touchend.stop.prevent="toggleSettings">
            <Settings class="icon" />
          </button>
          
          <Transition name="fade-slide">
            <div v-if="showSettings" class="settings-dropdown">
              <div class="menu-item" @click="toggleMouseMode" @touchend.stop.prevent="toggleMouseMode">
                <component :is="isMouseMode ? Presentation : Mouse" class="menu-icon" :size="18" />
                <span>{{ isMouseMode ? '退出鼠标模式' : '进入鼠标模式' }}</span>
              </div>
              <div class="menu-item" @click="toggleDragMode" @touchend.stop.prevent="toggleDragMode">
                <Mouse class="menu-icon" :size="18" />
                <span>{{ isDragMode ? '关闭拖拽模式' : '开启拖拽模式' }}</span>
              </div>
              <div class="menu-item logout" @click="handleLogout" @touchend.stop.prevent="handleLogout">
                <LogOut class="menu-icon" :size="18" />
                <span>退出登录</span>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </header>

    <!-- Main Touchpad Area -->
    <main class="main-content" :class="{ 'full-height': isMouseMode }">
      <div ref="touchpadRef" class="touchpad-area">
        <div class="touchpad-hint">
          <Hand class="hint-icon" />
          <div class="hint-text">
            <p>单指移动鼠标</p>
            <p>单指点击左键</p>
            <p>双指滑动滚动</p>
            <p>双指点击右键</p>
          </div>
        </div>
        <div class="touchpad-label">
          <div class="pulse-dot"></div>
          <span class="label-text">触控区域</span>
        </div>
      </div>
    </main>

    <!-- Footer Controls -->
    <footer v-if="!isMouseMode" class="footer">
      <button class="control-btn prev-btn" @click="handlePrev">
        <span class="btn-label">上一页</span>
        <span class="btn-sub-label">PREVIOUS</span>
      </button>
      <button class="control-btn next-btn" @click="handleNext">
        <span class="btn-label">下一页</span>
        <span class="btn-sub-label">NEXT SLIDE</span>
      </button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Sun, Moon, Settings, Hand, LogOut, Mouse, Presentation } from 'lucide-vue-next'
import { useTouchpad } from '../composables/useTouchpad'
import { useTheme } from '../composables/useTheme'
import { prevSlide, nextSlide, logout } from '../api'
import { isConnected, getLatency, disconnectSocket, connectSocket } from '../socket'

const isMouseMode = ref(false)
const isDragMode = ref(false)
const { touchpadRef, bindTouchEvents, unbindTouchEvents } = useTouchpad(() => isDragMode.value)

// 状态追踪
const isSocketConnected = ref(isConnected())
const isConnecting = ref(false)
const latency = ref(getLatency())
let statusTimer: any = null

const statusText = computed(() => {
  if (isSocketConnected.value) return '已连接'
  if (isConnecting.value) return '连接中...'
  return '未连接 (点击重连)'
})

// 设置菜单
const showSettings = ref(false)
function toggleSettings() {
  showSettings.value = !showSettings.value
}
function closeSettings() {
  showSettings.value = false
}

function toggleMouseMode() {
  isMouseMode.value = !isMouseMode.value
  showSettings.value = false
}

function toggleDragMode() {
  isDragMode.value = !isDragMode.value
  showSettings.value = false
}

async function handleLogout() {
  await logout()
  disconnectSocket()
  window.location.reload() // 刷新页面回到登录页
}

// 指令
const vClickOutside = {
  mounted(el: any, binding: any) {
    el._clickOutside = (event: Event) => {
      // 如果点击的是元素本身或其子元素，则不触发
      if (el === event.target || el.contains(event.target)) {
        return
      }
      binding.value(event)
    }
    // 使用 capture 模式，确保在冒泡到按钮的 stopPropagation 之前不会被意外触发
    // 或者干脆只监听 click，因为我们在按钮上已经处理了 touchend
    document.addEventListener('click', el._clickOutside)
    document.addEventListener('touchstart', el._clickOutside)
  },
  unmounted(el: any) {
    document.removeEventListener('click', el._clickOutside)
    document.removeEventListener('touchstart', el._clickOutside)
  }
}

// 暗色模式管理
const { isDark, toggleDarkMode } = useTheme()

// 初始化时同步一次状态
onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark')
})

function handlePrev() {
  prevSlide()
}

function handleNext() {
  nextSlide()
}

function handleReconnect() {
  if (isSocketConnected.value || isConnecting.value) return
  
  isConnecting.value = true
  connectSocket()
  
  // 3秒后如果还没连上，取消连接中状态
  setTimeout(() => {
    isConnecting.value = false
  }, 3000)
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible' && !isConnected()) {
    console.log('Page visible, attempting to reconnect socket...')
    handleReconnect()
  }
}

onMounted(() => {
  if (touchpadRef.value) {
    bindTouchEvents(touchpadRef.value)
  }

  // 监听可见性变化，实现自动重连
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  // 定时更新状态
  statusTimer = setInterval(() => {
    const connected = isConnected()
    isSocketConnected.value = connected
    if (connected) {
      isConnecting.value = false
    }
    latency.value = getLatency()
  }, 1000)
})

onUnmounted(() => {
  if (touchpadRef.value) {
    unbindTouchEvents(touchpadRef.value)
  }
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (statusTimer) {
    clearInterval(statusTimer)
  }
})
</script>

<style scoped>
.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.status-indicator:active {
  transform: scale(0.95);
  background: rgba(0, 0, 0, 0.1);
}

.dark .status-indicator {
  background: rgba(255, 255, 255, 0.1);
}

.status-indicator.connecting .dot {
  background-color: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

.main-content {
  flex: 1;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
}

.main-content.full-height {
  padding-bottom: 2rem;
}
</style>
