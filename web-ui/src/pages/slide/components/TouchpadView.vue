<template>
    <div class="touchpad-mode">
      <div class="touchpad-wrapper">
        <div ref="touchpadRef" class="touchpad-area">
          <div class="touchpad-hint">
            单指移动鼠标<br />
            单指点击左键<br />
            双指滑动滚动<br />
            双指点击右键
          </div>
        </div>
      </div>
      <div class="touchpad-controls">
        <button class="touchpad-btn" @click="handlePrev">上一页</button>
        <button class="touchpad-btn" @click="handleNext">下一页</button>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { onMounted, onUnmounted } from 'vue'
  import { useTouchpad } from '../composables/useTouchpad'
  import { prevSlide, nextSlide } from '../api'
  
  const { touchpadRef, bindTouchEvents, unbindTouchEvents } = useTouchpad()
  
  function handlePrev() {
    prevSlide()
  }
  
  function handleNext() {
    nextSlide()
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