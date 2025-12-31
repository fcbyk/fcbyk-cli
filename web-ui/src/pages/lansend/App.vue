<template>
  <div class="main-container">
    <!-- 文件列表容器（下载） -->
    <div class="file-container" :style="{ width: fileContainerWidth + 'px' }">
      <FileList
        :share-name="shareName"
        :path-parts="pathParts"
        :items="items"
        :loading="loading"
        :error="error"
        @navigate="navigateToPath"
        @item-click="handleItemClick"
      />
    </div>

    <!-- 可拖拽分隔条 -->
    <div 
      class="resizer" 
      @mousedown="startResize"
      @touchstart="startResize"
    ></div>

    <!-- 标签页容器（上传和预览） -->
    <div class="tabs-container" :style="{ width: tabsContainerWidth + 'px' }">
      <!-- 标签页头部 -->
      <div class="tabs-header">
        <div
          class="tab-item mobile-only"
          :class="{ active: activeTab === 'download' }"
          @click="activeTab = 'download'"
        >
          文件下载
        </div>
        <div
          class="tab-item"
          :class="{ active: activeTab === 'upload' }"
          @click="activeTab = 'upload'"
        >
          文件上传
        </div>
        <div
          class="tab-item"
          :class="{ active: activeTab === 'preview' }"
          @click="activeTab = 'preview'"
          :style="{ display: previewFile ? 'block' : 'none' }"
        >
          文件预览
        </div>
      </div>

      <!-- 标签页内容 -->
      <div class="tabs-content">
        <!-- 下载内容（移动端 Tab 展示；桌面端继续显示左侧列表） -->
        <div v-show="activeTab === 'download'" class="tab-pane download-pane">
          <FileList
            :share-name="shareName"
            :path-parts="pathParts"
            :items="items"
            :loading="loading"
            :error="error"
            @navigate="navigateToPath"
            @item-click="handleItemClick"
          />
        </div>

        <!-- 上传内容 -->
        <div v-show="activeTab === 'upload'" class="tab-pane">
          <UploadTab
            :can-upload="canUpload"
            :is-drag-over="isDragOver"
            :is-uploading="isUploading"
            :upload-hint="uploadHint"
            :require-password="requirePassword"
            v-model:password="password"
            :password-error="passwordError"
            :show-progress="showProgress"
            :queue-length="queueLength"
            :overall-progress="overallProgress"
            :upload-status="uploadStatus"
            :complete-info="completeInfo"
            :show-complete-info-flag="showCompleteInfoFlag"
            @verify-password="handleVerifyPassword"
            @files-selected="handleFiles"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
          />
        </div>

        <!-- 预览内容 -->
        <div v-show="activeTab === 'preview' && previewFile" class="tab-pane">
          <PreviewTab
            :preview-file="previewFile"
            :preview-loading="previewLoading"
            :preview-error="previewError"
            @close="closePreview"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import FileList from './components/FileList.vue'
import UploadTab from './components/UploadTab.vue'
import PreviewTab from './components/PreviewTab.vue'
import type { DirectoryItem } from './types'
import { useLansendDirectory } from './composables/useLansendDirectory'
import { useLansendUpload } from './composables/useLansendUpload'
import { useLansendPreview } from './composables/useLansendPreview'
import { sleep } from '@/utils/time'

// 目录
const {
  shareName,
  pathParts,
  items,
  loading,
  error,
  requirePassword,
  currentPath,
  loadDirectory,
  restorePathFromSession
} = useLansendDirectory()

// 上传
const {
  isDragOver,
  isUploading,
  password,
  passwordError,
  isPasswordVerified,
  canUpload: canUploadVerified,
  showProgress,
  queueLength,
  overallProgress,
  uploadHint,
  uploadStatus,
  completeInfo,
  showCompleteInfoFlag,
  verifyPassword,
  restorePasswordFromSession,
  enqueueFiles,
  processUploadQueue
} = useLansendUpload()

// 预览 + tab
const { previewFile, previewLoading, previewError, activeTab, previewFileContent, closePreview } = useLansendPreview()

// 根据后端 requirePassword 决定是否可上传
const canUpload = computed(() => {
  return !requirePassword.value || canUploadVerified.value
})

// 拖拽调整宽度相关
const fileContainerWidth = ref(400)
const tabsContainerWidth = ref(0)
const isResizing = ref(false)
const resizeStartX = ref(0)
const resizeStartFileWidth = ref(0)
const resizeStartTabsWidth = ref(0)

const isMobileLayout = ref(false)

function syncLayoutByWidth() {
  const mobile = window.matchMedia('(max-width: 768px)').matches
  // 从移动端切到桌面端时，不应继续停留在 download tab，否则会出现左右两边都是“文件下载”
  if (isMobileLayout.value && !mobile) {
    // 从移动端切到桌面端：左侧已经是“文件下载”，右侧就不要再停留在 download。
    if (activeTab.value === 'download') {
      activeTab.value = previewFile.value ? 'preview' : 'upload'
    }
  }
  isMobileLayout.value = mobile
}

// 初始化容器宽度
function initContainerWidths() {
  const container = document.querySelector('.main-container') as HTMLElement
  if (container) {
    const totalWidth = container.offsetWidth
    const savedFileWidth = sessionStorage.getItem('lansendFileContainerWidth')
    if (savedFileWidth && !isResizing.value) {
      const savedWidth = parseInt(savedFileWidth, 10)
      // 确保保存的宽度在合理范围内
      const minFileWidth = 200
      const maxFileWidth = totalWidth - 304 // 300 (tabs min) + 4 (resizer)
      const fileWidth = Math.max(minFileWidth, Math.min(maxFileWidth, savedWidth))
      fileContainerWidth.value = fileWidth
      tabsContainerWidth.value = totalWidth - fileWidth - 4 // 减去分隔条宽度
    } else if (!savedFileWidth) {
      fileContainerWidth.value = Math.floor(totalWidth * 0.4)
      tabsContainerWidth.value = totalWidth - fileContainerWidth.value - 4
    }
  }
}

// 开始拖拽调整
function startResize(e: MouseEvent | TouchEvent) {
  isResizing.value = true
  const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
  resizeStartX.value = clientX
  resizeStartFileWidth.value = fileContainerWidth.value
  resizeStartTabsWidth.value = tabsContainerWidth.value
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.addEventListener('touchmove', handleResize)
  document.addEventListener('touchend', stopResize)
  e.preventDefault()
}

// 处理拖拽调整
function handleResize(e: MouseEvent | TouchEvent) {
  if (!isResizing.value) return
  
  const container = document.querySelector('.main-container') as HTMLElement
  if (!container) return
  
  const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
  const deltaX = clientX - resizeStartX.value
  const containerRect = container.getBoundingClientRect()
  const newFileWidth = Math.max(200, Math.min(containerRect.width - 304, resizeStartFileWidth.value + deltaX))
  const newTabsWidth = containerRect.width - newFileWidth - 4 // 减去分隔条宽度
  
  fileContainerWidth.value = newFileWidth
  tabsContainerWidth.value = newTabsWidth
  
  // 保存到 sessionStorage
  sessionStorage.setItem('lansendFileContainerWidth', newFileWidth.toString())
  
  e.preventDefault()
}

// 停止拖拽调整
function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('touchmove', handleResize)
  document.removeEventListener('touchend', stopResize)
}

// 加载目录数据：由 useLansendDirectory 承担（这里保留一个薄封装，统一处理密码初始化）
async function loadDirectoryWithAuth(path: string = '') {
  const data = await loadDirectory(path)

  // 初始化密码验证
  if (requirePassword.value) {
    const storedPassword = restorePasswordFromSession()
    if (storedPassword) {
      await verifyPassword(storedPassword, true)
    }
  } else {
    // 不需要密码时视为已验证
    isPasswordVerified.value = true
  }

  return data
}

// 导航到指定路径
function navigateToPath(path: string) {
  loadDirectoryWithAuth(path)
  // 点击目录仅更新列表，不强制关闭预览、更不切换Tab。
  // 否则在移动端会频繁把用户从当前Tab“踢走”，体验很差。
}

// 处理文件/目录点击
async function handleItemClick(item: DirectoryItem) {
  if (item.is_dir) {
    // 点击目录，切换到该目录
    navigateToPath(item.path)
  } else {
    // 点击文件，预览文件内容
    await previewFileContent(item.path, item.name)
  }
}



// 处理密码验证
function handleVerifyPassword() {
  verifyPassword(password.value, false)
}

// 拖拽事件
function handleDragOver(e?: DragEvent) {
  if (!canUpload.value) return
  e?.preventDefault()
  isDragOver.value = true
}

function handleDragLeave(_e?: DragEvent) {
  if (!canUpload.value) return
  isDragOver.value = false
}

function handleDrop(e?: DragEvent) {
  if (!canUpload.value) return
  isDragOver.value = false
  if (e?.dataTransfer?.files) {
    handleFiles(Array.from(e.dataTransfer.files))
  }
}


// 处理文件上传
function handleFiles(files: File[]) {
  if (files.length === 0) return
  
  // 添加文件到上传队列
  enqueueFiles(files)
  
  // 开始处理上传队列
  processUploadQueue({
    currentPath: currentPath.value,
    requirePassword: requirePassword.value,
    getPassword: () => password.value,
    onWrongPassword: () => {
      passwordError.value = '密码错误，请重试'
    },
    onRefresh: async () => {
      // 上传完成后刷新目录
      await sleep(2000)
      loadDirectoryWithAuth(currentPath.value)
    }
  })
}

// 页面加载时获取数据
onMounted(() => {
  // 初始化容器宽度
  initContainerWidths()
  syncLayoutByWidth()

  // 监听窗口大小变化
  window.addEventListener('resize', initContainerWidths)
  window.addEventListener('resize', syncLayoutByWidth)

  // 移动端刷新时，默认展示“文件下载”Tab（桌面端左侧已有下载列表，右侧默认上传更合理）
  const mobile = window.matchMedia('(max-width: 768px)').matches
  if (mobile && !previewFile.value) {
    activeTab.value = 'download'
  }

  // 从会话存储恢复路径
  const initialPath = restorePathFromSession()
  loadDirectoryWithAuth(initialPath)
})

// 清理事件监听器
onBeforeUnmount(() => {
  window.removeEventListener('resize', initContainerWidths)
  window.removeEventListener('resize', syncLayoutByWidth)
})
</script>

