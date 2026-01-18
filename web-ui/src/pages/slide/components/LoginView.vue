<template>
  <div class="login-page">
    <header class="header">
      <div class="header-left">
      </div>
      <div class="header-right">
        <button class="icon-btn">
          <Sun class="icon-gray" :size="24" :stroke-width="1.5" />
        </button>
      </div>
    </header>

    <main class="main-content">
      <div class="title-section">
        <h1 class="main-title">SLIDE</h1>
        <p class="subtitle">准备好控制了吗？请输入访问密码</p>
      </div>

      <div class="input-section">
        <div class="input-wrapper">
          <Key class="input-icon" :size="20" :stroke-width="1.5" />
          <input
            ref="passwordInputRef"
            v-model="password"
            type="password"
            class="command-input"
            placeholder="••••••"
            autocomplete="off"
            @keypress.enter="handleLogin"
          />
        </div>
        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      </div>
    </main>

    <footer class="footer">
      <div class="slider-track" ref="sliderTrackRef">
        <div class="slider-text">右滑进入控制界面</div>
        <div
          class="slider-thumb"
          :class="{ 'dragging': isDragging }"
          :style="{ transform: `translateX(${sliderPosition}px)` }"
          @mousedown="startDrag"
          @touchstart="startDrag"
        >
          <ChevronRight :size="24" :stroke-width="1.5" />
        </div>
      </div>
    </footer>

    <div class="decorative-circle">
      <div class="semi-circle"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Sun, Key, ChevronRight } from 'lucide-vue-next'
import '@fontsource/syncopate/700.css'
import '@fontsource/space-mono/400.css'

interface Props {
  isLoading?: boolean
  errorMessage?: string
}

interface Emits {
  (e: 'login', password: string): void
  (e: 'clear-error'): void
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  errorMessage: ''
})

const emit = defineEmits<Emits>()

const password = ref('')
const passwordInputRef = ref<HTMLInputElement | null>(null)

// 监听输入变化，清除错误信息
watch(password, () => {
  if (props.errorMessage) {
    emit('clear-error')
  }
})

// 滑块逻辑
const sliderTrackRef = ref<HTMLElement | null>(null)
const sliderPosition = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const maxSliderDistance = ref(0)

function handleLogin() {
  if (props.isLoading) return
  
  // 触发登录
  emit('login', password.value)

  // 如果触发后依然不是加载状态（说明是同步失败，如空密码），手动重置滑块位置
  // 因为这种情况下 errorMessage 可能没有变化，导致 watch 不会触发
  nextTick(() => {
    if (!props.isLoading) {
      sliderPosition.value = 0
    }
  })
}

// 监听加载状态或错误消息，重置滑块
watch([() => props.isLoading, () => props.errorMessage], ([loading, error]) => {
  if (!loading || error) {
    sliderPosition.value = 0
  }
})

function startDrag(e: MouseEvent | TouchEvent) {
  if (props.isLoading) return
  isDragging.value = true
  startX.value = 'touches' in e ? e.touches[0].clientX : e.clientX
  
  if (sliderTrackRef.value) {
    const trackWidth = sliderTrackRef.value.clientWidth
    const thumbWidth = 52 // slider-thumb width
    maxSliderDistance.value = trackWidth - thumbWidth - 12 // 12 is padding (p-1.5 = 6px * 2)
  }

  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
  window.addEventListener('touchmove', onDrag, { passive: false })
  window.addEventListener('touchend', stopDrag)
}

function onDrag(e: MouseEvent | TouchEvent) {
  if (!isDragging.value) return
  
  // 阻止默认滚动行为
  if ('cancelable' in e && e.cancelable) {
    e.preventDefault()
  }

  const currentX = 'touches' in e ? e.touches[0].clientX : e.clientX
  const deltaX = currentX - startX.value
  
  sliderPosition.value = Math.max(0, Math.min(deltaX, maxSliderDistance.value))
  
  // 如果滑到最后，触发登录
  if (sliderPosition.value >= maxSliderDistance.value) {
    stopDrag()
    handleLogin()
  }
}

function stopDrag() {
  isDragging.value = false
  if (sliderPosition.value < maxSliderDistance.value) {
    sliderPosition.value = 0
  }
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('touchmove', onDrag)
  window.removeEventListener('touchend', stopDrag)
}

onMounted(() => {
  passwordInputRef.value?.focus()
})

onUnmounted(() => {
  stopDrag()
})
</script>

<style lang="scss" scoped>
.login-page {
  height: 100dvh;
  background-color: #F2F2F7;
  color: #1c1c1e;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  user-select: none;
}

.header {
  padding: 4vh 32px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  z-index: 10;
}

.icon-gray {
  color: #8E8E93;
}

.icon-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    opacity: 0.5;
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 40px;
  position: relative;
  min-height: 0; // 防止内容溢出
}

.title-section {
  text-align: center;
  margin-bottom: 8vh;
  
  .main-title {
    font-family: "Syncopate", sans-serif;
    font-size: clamp(48px, 12vw, 72px);
    font-weight: 700;
    letter-spacing: 0.25em;
    margin: 0 0 16px 0;
    padding-left: 0.25em;
    color: #1c1c1e;
  }

  .subtitle {
    font-size: 12px;
    letter-spacing: 0.1em;
    color: #8E8E93;
    font-weight: 500;
    margin: 0;
  }
}

.input-section {
  width: 100%;
  max-width: 320px;
  position: relative;

  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;

    .input-icon {
      position: absolute;
      left: 0;
      color: #C7C7CC;
    }

    .command-input {
      width: 100%;
      background: transparent;
      border: none;
      border-bottom: 2px solid #D1D1D6;
      padding: 16px 0 16px 40px;
      text-align: center;
      font-size: 24px;
      letter-spacing: 0.5em;
      color: #1c1c1e;
      transition: border-color 0.3s ease;
      outline: none;
      font-family: "Space Mono", monospace;

      &:focus {
        border-color: #007AFF;
      }

      &::placeholder {
        color: #D1D1D6;
      }
    }
  }

  .error-message {
    color: #FF3B30;
    font-size: 12px;
    margin-top: 8px;
    text-align: center;
    position: absolute;
    width: 100%;
  }
}

.footer {
  padding: 0 32px 8vh;
  width: 100%;
  max-width: 512px;
  margin: 0 auto;
  flex-shrink: 0;
  position: relative;

  .slider-track {
    position: relative;
    height: 64px;
    width: 100%;
    background: rgba(0, 0, 0, 0.04);
    backdrop-filter: blur(10px);
    border-radius: 32px;
    display: flex;
    align-items: center;
    padding: 6px;
    overflow: hidden;
    border: 1px solid rgba(0, 0, 0, 0.05);

    .slider-text {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      letter-spacing: 0.2em;
      color: #8E8E93;
      font-weight: 500;
      padding-left: 48px;
      pointer-events: none;
    }

    .slider-thumb {
      height: 52px;
      width: 52px;
      background-color: #007AFF;
      border-radius: 26px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(0, 122, 255, 0.4);
      border: 4px solid white;
      z-index: 10;
      transition: transform 0.3s cubic-bezier(0.2, 0, 0, 1), scale 0.2s;
      user-select: none;
      touch-action: none;

      &.dragging {
        transition: none;
      }

      &:active {
        scale: 0.95;
      }
    }
  }
}

.decorative-circle {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
  opacity: 0.5;

  .semi-circle {
    width: 300px;
    height: 150px;
    background: radial-gradient(circle at 50% 100%, rgba(0, 122, 255, 0.08) 0%, transparent 70%);
    border-top-left-radius: 150px;
    border-top-right-radius: 150px;
  }
}
</style>