<template>
  <div class="main-container flex flex-col md:flex-row gap-0 w-full max-w-full m-0 h-dvh max-h-dvh items-stretch relative p-2.5 md:p-3 min-h-0 overflow-hidden">
    <!-- 文件列表容器（目录） -->
    <div class="hidden md:flex flex-none min-w-[200px] max-w-[calc(100%-320px)] min-h-0 bg-white px-5 py-[15px] rounded-l-lg shadow-md flex-col h-full overflow-visible" :style="{ width: fileContainerWidth + 'px' }">
      <FileList
        :share-name="shareName"
        :path-parts="pathParts"
        :items="items"
        :loading="loading"
        :error="error"
        :un-download="unDownload"
        @navigate="navigateToPath"
        @item-click="handleItemClick"
      />
    </div>

    <!-- 可拖拽分隔条 -->
    <div class="hidden md:block w-1 bg-[#e4e7ed] cursor-col-resize flex-none relative transition-colors duration-200 z-10 hover:bg-[#409eff] before:content-[''] before:absolute before:-left-0.5 before:-right-0.5 before:top-0 before:bottom-0 before:cursor-col-resize" @mousedown="startResize" @touchstart="startResize"></div>

    <!-- 标签页容器（上传和预览） -->
    <div class="flex-auto min-w-0 min-h-0 bg-white rounded-lg md:rounded-l-none md:rounded-r-lg shadow-md flex flex-col h-full overflow-hidden relative" :style="!isMobileLayout ? { width: tabsContainerWidth + 'px' } : {}">
      <!-- 标签页头部 -->
      <div class="flex border-b border-[#e4e7ed] bg-white shrink-0 items-stretch overflow-x-auto overflow-y-hidden z-10">
        <div
          class="px-5 py-3 cursor-pointer text-[#606266] text-sm border-b-2 transition-all duration-300 select-none relative flex-none hover:text-[#409eff] block md:hidden"
          :class="activeTab === 'directory' ? 'text-[#409eff] border-b-[#409eff] font-medium' : 'border-transparent'"
          @click="activeTab = 'directory'"
        >
          文件夹
        </div>
        <div
          v-if="!unUpload"
          class="px-5 py-3 cursor-pointer text-[#606266] text-sm border-b-2 transition-all duration-300 select-none relative flex-none hover:text-[#409eff]"
          :class="activeTab === 'upload' ? 'text-[#409eff] border-b-[#409eff] font-medium' : 'border-transparent'"
          @click="activeTab = 'upload'"
        >
          上传
        </div>
        <div
          v-if="chatEnabled"
          class="px-5 py-3 cursor-pointer text-[#606266] text-sm border-b-2 transition-all duration-300 select-none relative flex-none hover:text-[#409eff]"
          :class="activeTab === 'chat' ? 'text-[#409eff] border-b-[#409eff] font-medium' : 'border-transparent'"
          @click="activeTab = 'chat'"
        >
          聊天
        </div>

        <!-- 单实例预览：tab 上展示当前预览文件名，并可关闭 -->
        <div
          class="px-5 py-3 cursor-pointer text-[#606266] text-sm border-b-2 transition-all duration-300 select-none relative flex-none hover:text-[#409eff] inline-flex items-center gap-2 max-w-[220px]"
          v-show="previewFile"
          :class="activeTab === 'preview' ? 'text-[#409eff] border-b-[#409eff] font-medium' : 'border-transparent'"
          @click="activeTab = 'preview'"
          :title="previewFile?.name"
        >
          <span class="overflow-hidden text-ellipsis whitespace-nowrap max-w-[170px]">{{ previewFile?.name }}</span>
          <button class="border-none bg-transparent text-[#909399] cursor-pointer p-0 w-[18px] h-[18px] leading-[18px] rounded flex items-center justify-center hover:bg-[#f0f0f0] hover:text-[#333]" @click.stop="closePreview" aria-label="关闭">×</button>
        </div>

        <!-- 测速按钮 -->
        <div class="ml-auto flex items-center gap-1 text-[#666] text-[13px] cursor-pointer px-5 py-3 md:px-3 border-l border-[#eee] hover:text-[#007bff] hover:bg-[#f8f9fa]" @click="startSpeedTest" title="局域网测速">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <span class="hidden md:inline">测速</span>
        </div>
      </div>

      <!-- 标签页内容 -->
      <div class="flex-1 overflow-hidden flex flex-col">
        <!-- 无上传功能时的空页 -->
        <div v-if="unUpload && activeTab === 'empty' && !previewFile" class="flex-1 flex items-center justify-center p-[15px] md:p-5">
          <div class="text-center text-[#9ca3af] text-sm leading-relaxed px-4 py-3 border border-dashed border-[#e5e7eb] rounded-[10px] bg-[#fafafa]">点击左侧文件进行预览</div>
        </div>
        <!-- 文件目录内容 -->
        <div v-show="activeTab === 'directory'" class="flex-1 flex flex-col overflow-hidden min-h-0 min-w-0">
          <FileList
            :share-name="shareName"
            :path-parts="pathParts"
            :items="items"
            :loading="loading"
            :error="error"
            :un-download="unDownload"
            @navigate="navigateToPath"
            @item-click="handleItemClick"
          />
        </div>

        <!-- 上传内容 -->
        <div v-if="!unUpload" v-show="activeTab === 'upload'" class="flex-1 flex flex-col overflow-hidden min-h-0 min-w-0">
          <UploadTab
            :can-upload="canUpload"
            :is-drag-over="isDragOver"
            :is-uploading="isUploading"
            :upload-hint="mainUploadHint"
            :upload-path-hint="uploadPathHint"
            :require-password="requirePassword"
            v-model:password="password"
            :password-error="passwordError"
            :show-progress="showProgress"
            :queue-length="queueLength"
            :overall-progress="overallProgress"
            :upload-status="uploadStatus"
            :upload-stats-text="uploadStatsText"
            :complete-info="completeInfo"
            :show-complete-info-flag="showCompleteInfoFlag"
            @verify-password="handleVerifyPassword"
            @files-selected="handleFiles"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
          />
        </div>

        <!-- 聊天内容 -->
        <div v-if="chatEnabled" v-show="activeTab === 'chat'" class="flex-1 flex flex-col overflow-hidden min-h-0 min-w-0 overscroll-contain touch-manipulation">
          <ChatTab />
        </div>
      </div>

      <!-- 预览层 -->
      <div v-show="activeTab === 'preview' && previewFile" class="absolute inset-0 z-5 bg-white flex flex-col pt-[45px]">
        <PreviewTab
          :preview-file="previewFile"
          :preview-loading="previewLoading"
          :preview-error="previewError"
          :video-loading="previewVideoLoading"
          @videoLoaded="onPreviewVideoLoaded"
          @videoError="onPreviewVideoError"
          @close="closePreview"
        />
      </div>
    </div>

    <!-- 测速卡片 -->
    <Transition name="slide-fade">
      <div v-if="isSpeedTestVisible" class="absolute top-[55px] md:top-[60px] right-2.5 md:right-5 w-[calc(100%-20px)] md:w-[280px] max-w-[300px] md:max-w-none bg-white rounded-xl shadow-2xl border border-[#eee] z-100 flex flex-col overflow-hidden">
        <div class="px-4 py-3 border-b border-[#eee] flex justify-between items-center bg-[#f8f9fa]">
          <h3 class="m-0 text-[15px] font-semibold text-[#333]">局域网测速</h3>
          <button class="border-none bg-none text-xl text-[#999] cursor-pointer leading-none p-1 hover:text-[#666]" @click="closeSpeedTest">×</button>
        </div>
        <div class="p-4 flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <span class="text-[13px] text-[#666]">延迟 (Ping):</span>
            <span class="text-sm font-semibold text-[#333] font-mono">{{ speedResult.ping }} ms</span>
          </div>
          <div class="flex flex-col gap-1.5">
            <div class="flex justify-between items-center">
              <span class="text-[13px]" :class="speedResult.status === 'downloading' ? 'text-[#007bff] font-semibold' : 'text-[#666]'">下载速度:</span>
              <span class="text-sm font-semibold text-[#333] font-mono">{{ formatSpeed(speedResult.download) }}</span>
            </div>
            <div v-if="speedResult.status === 'downloading'" class="h-1 bg-[#eee] rounded-sm overflow-hidden">
              <div class="h-full bg-[#007bff] transition-[width] duration-200 ease-out" :style="{ width: currentProgress + '%' }"></div>
            </div>
          </div>
          <div class="flex flex-col gap-1.5">
            <div class="flex justify-between items-center">
              <span class="text-[13px]" :class="speedResult.status === 'uploading' ? 'text-[#007bff] font-semibold' : 'text-[#666]'">上传速度:</span>
              <span class="text-sm font-semibold text-[#333] font-mono">{{ formatSpeed(speedResult.upload) }}</span>
            </div>
            <div v-if="speedResult.status === 'uploading'" class="h-1 bg-[#eee] rounded-sm overflow-hidden">
              <div class="h-full bg-[#007bff] transition-[width] duration-200 ease-out" :style="{ width: currentProgress + '%' }"></div>
            </div>
          </div>
          <div v-if="speedResult.status === 'error'" class="text-[12px] text-[#dc3545] p-2 bg-[#fff5f5] rounded">
            {{ speedResult.error }}
          </div>

          <div v-if="speedResult.status === 'completed'" class="mt-2 p-3 bg-[#f0f7ff] rounded-lg border border-[#d0e7ff]">
            <div class="text-[12px] text-[#666] mb-2">传输 1GB 文件预计耗时：</div>
            <div class="flex gap-3">
              <div class="flex-1 flex flex-col gap-0.5">
                <span class="text-[11px] text-[#999]">下载</span>
                <span class="text-sm font-semibold text-[#0056b3]">{{ formatDuration(1024 * 1024 * 1024 / speedResult.download) }}</span>
              </div>
              <div class="flex-1 flex flex-col gap-0.5">
                <span class="text-[11px] text-[#999]">上传</span>
                <span class="text-sm font-semibold text-[#0056b3]">{{ formatDuration(1024 * 1024 * 1024 / speedResult.upload) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="p-3 border-t border-[#eee]">
          <button 
            class="w-full p-2 bg-[#007bff] text-white border-none rounded-md text-sm cursor-pointer transition-colors duration-200 hover:bg-[#0056b3] disabled:bg-[#ccc] disabled:cursor-not-allowed" 
            :disabled="speedResult.status !== 'completed' && speedResult.status !== 'error' && speedResult.status !== 'idle'"
            @click="startSpeedTest"
          >
            {{ speedResult.status === 'completed' || speedResult.status === 'error' ? '重新测速' : '正在测速...' }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onBeforeUnmount } from 'vue'
import FileList from './components/FileList.vue'
import UploadTab from './components/UploadTab.vue'
import PreviewTab from './components/PreviewTab.vue'
import ChatTab from './components/ChatTab.vue'
import type { DirectoryItem } from './types'
import { useLansendDirectory } from './composables/useLansendDirectory'
import { useLansendUpload } from './composables/useLansendUpload'
import { useLansendPreview } from './composables/useLansendPreview'
import { useLansendSpeed } from './composables/useLansendSpeed'
import { getLansendConfig } from './api'
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
  restorePathFromSession,
  startPolling,
  stopPolling
} = useLansendDirectory()

// 获取配置
const unDownload = ref(false)
const unUpload = ref(false)
const chatEnabled = ref(false)
onMounted(async () => {
  try {
    const config = await getLansendConfig()
    unDownload.value = config.un_download === true
    unUpload.value = config.un_upload === true
    chatEnabled.value = config.chat_enabled === true
    
    if (unUpload.value) {
      activeTab.value = previewFile.value ? 'preview' : 'empty'
      
      if (isMobileLayout.value) {
        activeTab.value = 'directory'
      }
    }
  } catch (e) {
    console.error('Failed to fetch config:', e)
  }
})

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
  uploadStatsText,
  completeInfo,
  showCompleteInfoFlag,
  verifyPassword,
  restorePasswordFromSession,
  enqueueFiles,
  processUploadQueue
} = useLansendUpload()

// 预览 + tab（单实例预览）
const {
  previewFile,
  previewLoading,
  previewError,
  activeTab,
  previewVideoLoading,
  previewFileContent,
  closePreview: originalClosePreview,
  onPreviewVideoLoaded,
  onPreviewVideoError
} = useLansendPreview()

// 测速
const {
  isSpeedTestVisible,
  speedResult,
  currentProgress,
  startSpeedTest,
  closeSpeedTest,
  formatSpeed,
  formatDuration
} = useLansendSpeed()

// 根据后端 requirePassword 决定是否可上传
const canUpload = computed(() => {
  return !requirePassword.value || canUploadVerified.value
})

// 构建当前上传目录的显示路径
const currentUploadPath = computed(() => {
  if (!shareName.value) return ''
  const parts = pathParts.value.map(p => p.name).join('/')
  if (parts) {
    return `/${shareName.value}/${parts}`
  }
  return `/${shareName.value}`
})

const mainUploadHint = computed(() => {
  return uploadHint.value
})

const uploadPathHint = computed(() => {
  const path = currentUploadPath.value
  if (!path) return ''
  return `文件将上传到：${path}`
})

// 关闭预览：无上传功能时回到空白提示页
function closePreview() {
  originalClosePreview({ unUpload: unUpload.value })
}

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
  // 从移动端切到桌面端时，不应继续停留在 directory tab，否则会出现左右两边都是"文件目录"
  if (isMobileLayout.value && !mobile) {
    // 从移动端切到桌面端：左侧已经是"文件目录"，右侧就不要再停留在 directory。
    if (activeTab.value === 'directory') {
      activeTab.value = previewFile.value ? 'preview' : (unUpload.value ? 'empty' : 'upload')
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
    // 点击文件：单实例预览（直接切换内容）
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

  // 上传时暂停轮询，避免冲突
  stopPolling()

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
      // 上传完成后恢复轮询
      startPolling()
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

  // 移动端刷新时，默认展示"文件目录"Tab（桌面端左侧已有目录列表，右侧默认上传更合理）
  const mobile = window.matchMedia('(max-width: 768px)').matches
  if (mobile && !previewFile.value) {
    activeTab.value = 'directory'
  }

  // 从会话存储恢复路径
  const initialPath = restorePathFromSession()
  loadDirectoryWithAuth(initialPath).then(() => {
    // 加载完成后开始轮询
    startPolling()
  })
})

// 清理事件监听器
onBeforeUnmount(() => {
  window.removeEventListener('resize', initContainerWidths)
  window.removeEventListener('resize', syncLayoutByWidth)
  // 停止轮询
  stopPolling()
})
</script>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>