import { computed, ref } from 'vue'
import { verifyUploadPassword, uploadFile } from '../api'
import { sleep } from '@/utils/time'
import { formatFileSize } from '@/utils/files'

let completeInfoTimer: ReturnType<typeof setTimeout> | null = null

const PASSWORD_KEY = 'lansendUploadPassword'

type UploadQueueParams = {
  currentPath: string
  requirePassword: boolean
  getPassword: () => string
  onWrongPassword?: () => void
  onRefresh?: () => void
}

export function useLansendUpload() {
  // 上传相关
  const isDragOver = ref(false)
  const isUploading = ref(false)
  const password = ref('')
  const passwordError = ref('')
  const isPasswordVerified = ref(false)

  // 上传队列
  const uploadQueue = ref<File[]>([])
  const totalFiles = ref(0)
  const uploadedCount = ref(0)
  const renamedFiles = ref<string[]>([])
  const currentFileProgress = ref(0)
  const currentFileName = ref('')
  const currentFileSize = ref(0)
  const currentFileLoaded = ref(0)
  const completeInfo = ref('')
  const showCompleteInfoFlag = ref(false)

  const canUpload = computed(() => isPasswordVerified.value)

  const showProgress = computed(() => uploadQueue.value.length > 0 || isUploading.value)

  const queueLength = computed(() => uploadQueue.value.length)

  // overallProgress 以“字节”加权：避免 5GB + 5MB 时两者各占 50% 的错觉
  const totalBytes = ref(0)
  const uploadedBytes = ref(0)

  const overallProgress = computed(() => {
    if (totalBytes.value === 0) return 0
    const currentBytes = currentFileLoaded.value || 0
    const p = ((uploadedBytes.value + currentBytes) / totalBytes.value) * 100
    return Math.min(100, Math.max(0, p))
  })

  const uploadHint = computed(() => {
    return isUploading.value ? '上传中...可继续拖拽文件添加到队列' : '拖拽文件到此处或点击选择文件'
  })

  // 速度/剩余时间估算：使用整体已上传字节数做平滑计算
  const startedAtMs = ref<number | null>(null)
  const lastTickAtMs = ref<number | null>(null)
  const lastUploadedTotalBytes = ref(0)
  const uploadSpeedBytesPerSec = ref(0)

  const uploadedTotalBytes = computed(() => uploadedBytes.value + (currentFileLoaded.value || 0))
  const remainingBytes = computed(() => Math.max(0, totalBytes.value - uploadedTotalBytes.value))

  const etaSeconds = computed(() => {
    const speed = uploadSpeedBytesPerSec.value
    if (!isUploading.value || speed <= 0) return null
    return Math.ceil(remainingBytes.value / speed)
  })

  function formatDuration(seconds: number) {
    if (!Number.isFinite(seconds) || seconds < 0) return ''
    const s = Math.floor(seconds % 60)
    const m = Math.floor((seconds / 60) % 60)
    const h = Math.floor(seconds / 3600)
    if (h > 0) return `${h}h ${m}m ${s}s`
    if (m > 0) return `${m}m ${s}s`
    return `${s}s`
  }

  const uploadStatsText = computed(() => {
    if (!showProgress.value) return ''
    const total = totalBytes.value
    const uploaded = uploadedTotalBytes.value
    const remain = remainingBytes.value
    const speed = uploadSpeedBytesPerSec.value

    const parts: string[] = []
    if (total > 0) parts.push(`总 ${formatFileSize(total)}`)
    if (uploaded > 0 || isUploading.value) parts.push(`已传 ${formatFileSize(uploaded)}`)
    if (remain > 0) parts.push(`剩余 ${formatFileSize(remain)}`)
    if (isUploading.value && speed > 0) parts.push(`速度 ${formatFileSize(speed)}/s`)
    if (isUploading.value && etaSeconds.value != null) parts.push(`预计 ${formatDuration(etaSeconds.value)}`)
    return parts.join(' · ')
  })

  function showCompleteInfo(uploaded: number, renamed: number) {
    // 避免上一次的定时器把本次的提示提前清掉
    if (completeInfoTimer) {
      clearTimeout(completeInfoTimer)
      completeInfoTimer = null
    }

    showCompleteInfoFlag.value = true
    completeInfo.value = `已成功上传 ${uploaded} 个文件`
    if (renamed > 0) {
      completeInfo.value += `，${renamed} 个文件因重名已自动重命名`
    }

    completeInfoTimer = setTimeout(() => {
      showCompleteInfoFlag.value = false
      completeInfo.value = ''
      completeInfoTimer = null
    }, 15000)
  }

  const uploadStatus = computed(() => {
    if (uploadedCount.value === 0 && !isUploading.value) return ''

    if (uploadedCount.value === totalFiles.value && !isUploading.value) {
      if (renamedFiles.value.length > 0) {
        return `全部完成！已上传 ${uploadedCount.value} 个文件，${renamedFiles.value.length} 个文件因重名已自动重命名`
      }
      return `全部完成！已上传 ${uploadedCount.value} 个文件`
    }

    if (currentFileName.value && currentFileSize.value > 0) {
      const uploadedSize = formatFileSize(currentFileLoaded.value)
      const totalSize = formatFileSize(currentFileSize.value)
      return `正在上传: ${currentFileName.value} (${uploadedSize} / ${totalSize}) - ${Math.round(currentFileProgress.value)}%`
    }

    if (currentFileName.value) {
      return `正在上传: ${currentFileName.value} - ${Math.round(currentFileProgress.value)}%`
    }

    if (renamedFiles.value.length > 0) {
      return `已上传 ${uploadedCount.value}/${totalFiles.value} 个文件，${renamedFiles.value.length} 个文件因重名已自动重命名`
    }

    return `已上传 ${uploadedCount.value}/${totalFiles.value} 个文件`
  })

  async function verifyPassword(passwordToVerify: string, isAuto = false) {
    if (!passwordToVerify.trim()) {
      if (!isAuto) passwordError.value = '请输入密码'
      return false
    }

    passwordError.value = ''

    const result = await verifyUploadPassword(passwordToVerify)
    if (result.success) {
      isPasswordVerified.value = true
      password.value = passwordToVerify
      sessionStorage.setItem(PASSWORD_KEY, passwordToVerify)
      return true
    }

    passwordError.value = result.error || '密码错误，请重试'
    sessionStorage.removeItem(PASSWORD_KEY)
    isPasswordVerified.value = false
    return false
  }

  function restorePasswordFromSession() {
    const storedPassword = sessionStorage.getItem(PASSWORD_KEY)
    if (storedPassword) {
      password.value = storedPassword
      return storedPassword
    }
    return null
  }

  function resetUploadState() {
    isUploading.value = false
    isDragOver.value = false

    uploadQueue.value = []
    totalFiles.value = 0
    totalBytes.value = 0

    uploadedCount.value = 0
    uploadedBytes.value = 0

    renamedFiles.value = []
    currentFileProgress.value = 0
    currentFileName.value = ''
    currentFileSize.value = 0
    currentFileLoaded.value = 0
  }

  function enqueueFiles(files: File[]) {
    if (files.length === 0) return
    uploadQueue.value.push(...files)
    totalFiles.value += files.length
    totalBytes.value += files.reduce((sum, f) => sum + (f.size || 0), 0)
  }

  let processingPromise: Promise<void> | null = null

  async function processUploadQueue(params: UploadQueueParams) {
    // 防重入：上传过程中再次 enqueue 会再次触发 processUploadQueue，从而并发上传、UI 闪烁
    if (processingPromise) return processingPromise

    processingPromise = (async () => {
      showCompleteInfoFlag.value = false
      isUploading.value = true

      // 进入上传循环时启动速度统计
      const now0 = Date.now()
      startedAtMs.value = startedAtMs.value ?? now0
      lastTickAtMs.value = now0
      lastUploadedTotalBytes.value = uploadedTotalBytes.value
      uploadSpeedBytesPerSec.value = 0

      while (uploadQueue.value.length > 0) {
        const file = uploadQueue.value.shift()!

        currentFileProgress.value = 0
        currentFileName.value = file.name
        currentFileSize.value = file.size
        currentFileLoaded.value = 0

        const result = await uploadFile(
          file,
          params.currentPath,
          params.requirePassword ? params.getPassword() : null,
          (progress, meta) => {
            currentFileProgress.value = progress
            if (meta) {
              currentFileLoaded.value = meta.loaded
              currentFileSize.value = meta.total
            } else {
              currentFileLoaded.value = (file.size * progress) / 100
            }

            // 每隔一段时间更新一次速度（平滑一些，避免闪烁）
            const now = Date.now()
            if (lastTickAtMs.value == null || lastUploadedTotalBytes.value == null) {
              lastTickAtMs.value = now
              lastUploadedTotalBytes.value = uploadedTotalBytes.value
              return
            }
            if (now - lastTickAtMs.value < 800) return

            const deltaBytes = uploadedTotalBytes.value - lastUploadedTotalBytes.value
            const deltaSec = (now - lastTickAtMs.value) / 1000
            if (deltaSec > 0 && deltaBytes >= 0) {
              const inst = deltaBytes / deltaSec
              uploadSpeedBytesPerSec.value = uploadSpeedBytesPerSec.value > 0
                ? uploadSpeedBytesPerSec.value * 0.7 + inst * 0.3
                : inst
            }
            lastTickAtMs.value = now
            lastUploadedTotalBytes.value = uploadedTotalBytes.value
          }
        )

        if (!result.success) {
          if (result.error === 'wrong password') {
            isPasswordVerified.value = false
            isUploading.value = false
            passwordError.value = '密码错误，请重试'
            sessionStorage.removeItem(PASSWORD_KEY)
            params.onWrongPassword?.()
            return
          }

          if (result.error === 'upload password required') {
            isPasswordVerified.value = false
            isUploading.value = false
            return
          }

          // 其他错误：跳过该文件继续下一个
          continue
        }

        uploadedCount.value++
        uploadedBytes.value += file.size
        currentFileProgress.value = 100

        if (result.data?.renamed) {
          renamedFiles.value.push(result.data.filename)
        }
      }

      // 队列真正清空后再 refresh + 提示
      const uploaded = uploadedCount.value
      const renamed = renamedFiles.value.length

      params.onRefresh?.()
      await sleep(2000)
      showCompleteInfo(uploaded, renamed)

      // 重置队列状态（含 totalBytes），避免下一轮进度被“平均/稀释”
      uploadedCount.value = 0
      uploadedBytes.value = 0
      renamedFiles.value = []
      totalFiles.value = 0
      totalBytes.value = 0
      currentFileProgress.value = 0
      currentFileName.value = ''
      currentFileSize.value = 0
      currentFileLoaded.value = 0
      startedAtMs.value = null
      lastTickAtMs.value = null
      lastUploadedTotalBytes.value = 0
      uploadSpeedBytesPerSec.value = 0
      isUploading.value = false
    })().finally(() => {
      processingPromise = null
    })

    return processingPromise
  }

  return {
    // state
    isDragOver,
    isUploading,
    password,
    passwordError,
    isPasswordVerified,

    uploadQueue,
    totalFiles,
    totalBytes,
    uploadedCount,
    uploadedBytes,
    renamedFiles,
    currentFileProgress,
    currentFileName,
    currentFileSize,
    currentFileLoaded,

    uploadStatsText,

    completeInfo,
    showCompleteInfoFlag,

    // computed
    canUpload,
    showProgress,
    queueLength,
    overallProgress,
    uploadHint,
    uploadStatus,

    // actions
    verifyPassword,
    restorePasswordFromSession,
    resetUploadState,
    enqueueFiles,
    processUploadQueue
  }
}
