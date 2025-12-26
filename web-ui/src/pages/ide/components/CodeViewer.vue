<template>
  <div class="code-viewer">
    <div class="code-header">
      <div class="code-title">
        <button
          class="menu-btn"
          :class="{ 'menu-btn-hidden': isMobile && isSidebarOpen }"
          @click="$emit('toggle-sidebar')"
        >
          ☰
        </button>
        <span class="code-title-text">
          {{ currentFile ? fileName : '选择一个文件查看代码' }}
        </span>
      </div>
      <div style="display: flex; align-items: center;">
        <div v-if="currentFile && !isMobile" class="font-size-controls">
          <button
            class="close-btn"
            title="关闭文件"
            @click="$emit('close-file')"
          >
            ×
          </button>
          <button
            class="font-size-btn"
            title="减小字体"
            :disabled="fontSize <= minFontSize"
            @click="$emit('decrease-font')"
          >
            −
          </button>
          <button
            class="font-size-btn"
            title="增大字体"
            :disabled="fontSize >= maxFontSize"
            @click="$emit('increase-font')"
          >
            +
          </button>
        </div>
        <!-- 移动端下拉菜单 -->
        <div v-if="showDropdownMenu" class="dropdown-menu">
          <button
            class="dropdown-btn"
            title="更多操作"
            @click.stop="$emit('toggle-dropdown')"
          >
            ⋮
          </button>
          <div
            v-if="isDropdownOpen"
            class="dropdown-content show"
            @click.stop
          >
            <button
              class="dropdown-item"
              title="关闭文件"
              @click="$emit('close-file'); $emit('toggle-dropdown')"
            >
              关闭文件
            </button>
            <div class="dropdown-divider"></div>
            <button
              class="dropdown-item"
              title="复制代码"
              @click="$emit('copy-code'); $emit('toggle-dropdown')"
            >
              复制代码
            </button>
            <div class="dropdown-divider"></div>
            <button
              class="dropdown-item"
              :class="{ disabled: fontSize <= minFontSize }"
              title="减小字体"
              :disabled="fontSize <= minFontSize"
              @click="$emit('decrease-font')"
            >
              减小字体
            </button>
            <button
              class="dropdown-item"
              :class="{ disabled: fontSize >= maxFontSize }"
              title="增大字体"
              :disabled="fontSize >= maxFontSize"
              @click="$emit('increase-font')"
            >
              增大字体
            </button>
          </div>
        </div>
        <button
          class="refresh-btn"
          :class="{ refreshing: isRefreshing }"
          :title="currentFile ? '刷新当前文件: ' + fileName.split('/').pop() : '刷新目录树'"
          :disabled="isRefreshing"
          @click="$emit('refresh')"
        >
          <span class="refresh-icon">⟳</span>
        </button>
        <button
          v-if="currentFile && !isMobile"
          class="copy-btn"
          :class="{ copied: copyButtonText === 'Copied!' }"
          @click="$emit('copy-code')"
        >
          {{ copyButtonText }}
        </button>
        <div class="theme-toggle">
          <label class="theme-switch">
            <input
              type="checkbox"
              :checked="isLightTheme"
              @change="$emit('toggle-theme')"
            />
            <span class="theme-slider"></span>
          </label>
        </div>
      </div>
    </div>
    <div class="code-content">
      <div v-if="!currentFile" class="empty-state">
        请从左侧选择文件查看代码
      </div>
      <div v-else-if="!fileContent && fileName" class="empty-state">
        {{ fileName }}
      </div>
      <div v-else-if="fileContent" class="code-wrapper">
        <div ref="lineNumbersRef" class="line-numbers"></div>
        <pre ref="codePreRef"><code>{{ fileContent }}</code></pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  currentFile: string | null
  fileContent: string
  fileName: string
  fontSize: number
  isLightTheme: boolean
  isSidebarOpen: boolean
  isDropdownOpen: boolean
  isRefreshing: boolean
  copyButtonText: string
  showDropdownMenu: boolean
}>()

const emit = defineEmits<{
  'close-file': []
  'copy-code': []
  'decrease-font': []
  'increase-font': []
  'refresh': []
  'toggle-dropdown': []
  'toggle-theme': []
  'toggle-sidebar': []
}>()

const lineNumbersRef = ref<HTMLElement | null>(null)
const codePreRef = ref<HTMLElement | null>(null)

const minFontSize = 10
const maxFontSize = 24

const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value <= 768)

// 监听窗口大小变化
function handleResize() {
  windowWidth.value = window.innerWidth
}

// 应用字体大小
function applyFontSize(size: number) {
  if (codePreRef.value) {
    codePreRef.value.style.fontSize = size + 'px'
  }
  if (lineNumbersRef.value) {
    lineNumbersRef.value.style.fontSize = size + 'px'
  }
}

// 渲染代码（更新行号）
function updateLineNumbers() {
  if (!props.fileContent || !lineNumbersRef.value) return

  const lines = props.fileContent.split('\n')
  let lineNumbersHtml = ''
  for (let i = 1; i <= lines.length; i++) {
    lineNumbersHtml += `<span class="line-number">${i}</span>\n`
  }
  lineNumbersRef.value.innerHTML = lineNumbersHtml
  applyFontSize(props.fontSize)
}

// 监听文件内容变化
watch(
  () => props.fileContent,
  () => {
    updateLineNumbers()
  },
  { immediate: true }
)

// 监听字体大小变化
watch(
  () => props.fontSize,
  (newSize) => {
    applyFontSize(newSize)
  }
)

// 点击外部关闭下拉菜单
onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
  
  document.addEventListener('click', (e) => {
    if (props.isDropdownOpen && !(e.target as HTMLElement).closest('.dropdown-content') && !(e.target as HTMLElement).closest('.dropdown-btn')) {
      emit('toggle-dropdown')
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// 暴露方法给父组件
defineExpose({
  applyFontSize,
  updateLineNumbers
})
</script>
