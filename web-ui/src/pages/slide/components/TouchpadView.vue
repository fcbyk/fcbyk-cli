<template>
  <div class="control-interface">
    <!-- Header -->
    <header class="header">
      <div class="status-indicator">
        <div class="dot"></div>
        <span class="status-text">已连接</span>
      </div>
      <div class="header-actions">
        <button class="icon-btn" @click="toggleDarkMode">
          <component :is="isDark ? Moon : Sun" class="icon" />
        </button>
        <button class="icon-btn">
          <Settings class="icon" />
        </button>
      </div>
    </header>

    <!-- Main Touchpad Area -->
    <main class="main-content">
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
    <footer class="footer">
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
import { ref, onMounted, onUnmounted } from 'vue'
import { Sun, Moon, Settings, Hand } from 'lucide-vue-next'
import { useTouchpad } from '../composables/useTouchpad'
import { prevSlide, nextSlide } from '../api'

const { touchpadRef, bindTouchEvents, unbindTouchEvents } = useTouchpad()

// 暗色模式状态
const isDark = ref(document.documentElement.classList.contains('dark'))

function handlePrev() {
  prevSlide()
}

function handleNext() {
  nextSlide()
}

function toggleDarkMode() {
  document.documentElement.classList.toggle('dark')
  isDark.value = document.documentElement.classList.contains('dark')
}

onMounted(() => {
  if (touchpadRef.value) {
    bindTouchEvents(touchpadRef.value)
  }
})

onUnmounted(() => {
  if (touchpadRef.value) {
    unbindTouchEvents(touchpadRef.value)
  }
})
</script>