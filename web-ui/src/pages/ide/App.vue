<template>
  <div class="main-app">
    <div
      class="sidebar-overlay"
      :class="{ active: isSidebarOpen }"
      @click="closeSidebar"
    ></div>
    <div class="main-container">
      <SidebarArea
        :file-tree="fileTree"
        :sidebar-width="sidebarWidth"
        :is-sidebar-open="isSidebarOpen"
        :active-file="currentFile"
        @file-selected="handleFileSelected"
        @toggle-sidebar="toggleSidebar"
        @sidebar-resize="handleSidebarResize"
      />
      <CodeViewer
        :current-file="currentFile"
        :file-content="fileContent"
        :file-name="fileName"
        :font-size="fontSize"
        :is-light-theme="isLightTheme"
        :is-sidebar-open="isSidebarOpen"
        :is-dropdown-open="isDropdownOpen"
        :is-refreshing="isRefreshing"
        :copy-button-text="copyButtonText"
        :show-dropdown-menu="showDropdownMenu"
        @close-file="closeFile"
        @copy-code="handleCopyCode"
        @decrease-font="decreaseFontSize"
        @increase-font="increaseFontSize"
        @refresh="handleRefresh"
        @toggle-dropdown="toggleDropdown"
        @toggle-theme="toggleTheme"
        @toggle-sidebar="toggleSidebar"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import SidebarArea from './components/SidebarArea.vue'
import CodeViewer from './components/CodeViewer.vue'

// 响应式状态
const fileTree = ref<any[]>([])
const currentFile = ref<string | null>(null)
const fileContent = ref<string>('')
const fileName = ref<string>('')
const fontSize = ref<number>(
  parseInt(localStorage.getItem('codeFontSize') || '', 10) || 14
)
const isLightTheme = ref<boolean>(localStorage.getItem('theme') === 'light')
const sidebarWidth = ref<number>(
  parseInt(localStorage.getItem('sidebarWidth') || '', 10) || 300
)
const isSidebarOpen = ref<boolean>(false)
const isDropdownOpen = ref<boolean>(false)
const isRefreshing = ref<boolean>(false)
const copyButtonText = ref<string>('copy')

// 常量
const minFontSize = 10
const maxFontSize = 24
const fontSizeStep = 2

// 模板引用

// 计算属性
const showDropdownMenu = computed(() => {
  return currentFile.value !== null && window.innerWidth <= 768
})



// 复制到剪贴板
async function copyToClipboard(text: string) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      return fallbackCopyToClipboard(text)
    }
  }
  return fallbackCopyToClipboard(text)
}

function fallbackCopyToClipboard(text: string) {
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    textarea.style.left = '-9999px'
    document.body.appendChild(textarea)
    textarea.select()
    const success = document.execCommand('copy')
    document.body.removeChild(textarea)
    return success
  } catch {
    return false
  }
}

// 加载文件内容
async function loadFile(path: string) {
  currentFile.value = path
  fileContent.value = ''
  fileName.value = ''

  try {
    const response = await fetch('/' + encodeURIComponent(path))
    if (!response.ok) {
      throw new Error('文件加载失败')
    }

    const data = await response.json()

    if (data.error) {
      fileContent.value = ''
      fileName.value = data.error
      return
    }

    fileName.value = data.name || path
    fileContent.value = data.content
  } catch (error) {
    console.error('加载文件失败:', error)
    fileContent.value = ''
    fileName.value = '加载失败，请重试'
  }
}

// 关闭当前文件
function closeFile() {
  currentFile.value = null
  fileContent.value = ''
  fileName.value = ''
  isDropdownOpen.value = false
}

// 获取目录树
async function loadFileTree() {
  try {
    const response = await fetch('/api/tree')
    const data = await response.json()
    if (data.tree) {
      fileTree.value = data.tree
    }
  } catch (error) {
    console.error('加载目录树失败:', error)
  }
}

// 应用字体大小
function applyFontSize(size: number) {
  size = Math.max(minFontSize, Math.min(maxFontSize, size))
  fontSize.value = size
  localStorage.setItem('codeFontSize', size.toString())
}

// 减小字体
function decreaseFontSize() {
  if (fontSize.value > minFontSize) {
    applyFontSize(fontSize.value - fontSizeStep)
  }
}

// 增大字体
function increaseFontSize() {
  if (fontSize.value < maxFontSize) {
    applyFontSize(fontSize.value + fontSizeStep)
  }
}

// 处理文件选择
function handleFileSelected(path: string) {
  loadFile(path)
  if (window.innerWidth <= 768) {
    setTimeout(() => {
      closeSidebar()
    }, 100)
  }
}

// 处理复制代码
async function handleCopyCode() {
  if (!fileContent.value) return

  const success = await copyToClipboard(fileContent.value)
  if (success) {
    copyButtonText.value = 'Copied!'
    setTimeout(() => {
      copyButtonText.value = 'copy'
    }, 2000)
  } else {
    alert('复制失败，请手动选择复制')
  }
}

// 处理刷新
async function handleRefresh() {
  if (isRefreshing.value) return
  isRefreshing.value = true

  try {
    if (currentFile.value) {
      await loadFile(currentFile.value)
    } else {
      await loadFileTree()
    }
  } catch (error) {
    console.error('刷新失败:', error)
  } finally {
    setTimeout(() => {
      isRefreshing.value = false
    }, 500)
  }
}

// 切换下拉菜单
function toggleDropdown() {
  isDropdownOpen.value = !isDropdownOpen.value
}

// 切换侧边栏
function toggleSidebar() {
  isSidebarOpen.value = !isSidebarOpen.value
  if (isSidebarOpen.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}

// 关闭侧边栏
function closeSidebar() {
  isSidebarOpen.value = false
  document.body.style.overflow = ''
}

// 切换主题
function toggleTheme() {
  isLightTheme.value = !isLightTheme.value
  if (isLightTheme.value) {
    document.body.classList.add('light-theme')
    localStorage.setItem('theme', 'light')
  } else {
    document.body.classList.remove('light-theme')
    localStorage.setItem('theme', 'dark')
  }
}

// 处理侧边栏调整大小
function handleSidebarResize(width: number) {
  sidebarWidth.value = width
  localStorage.setItem('sidebarWidth', width.toString())
}

// 监听窗口大小变化
watch(
  () => window.innerWidth,
  () => {
    // 响应式更新会在 computed 中处理
  }
)

// 初始化主题
onMounted(() => {
  if (isLightTheme.value) {
    document.body.classList.add('light-theme')
  } else {
    document.body.classList.remove('light-theme')
  }

  loadFileTree()
})
</script>
