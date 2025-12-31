import { computed, ref } from 'vue'
import { verifyUploadPassword, uploadFile } from '../api'

const PASSWORD_KEY = 'lansendUploadPassword'

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

  const canUpload = computed(() => {
    return isPasswordVerified.value
  })

  const showProgress = computed(() => {
    return uploadQueue.value.length > 0 || isUploading.value
  })

  const queueLength = computed(() => {
    return uploadQueue.value.length
  })

  const overallProgress = computed(() => {
    if (totalFiles.value === 0) return 0
    const baseProgress = (uploadedCount.value / totalFiles.value) * 100
    const currentProgress = currentFileProgress.value / totalFiles.value
    return Math.min(baseProgress + currentProgress, 100)
  })

  const uploadHint = computed(() => {
    if (isUploading.value) {
      return '上传中...可继续拖拽文件添加到队列'
    }
    return '拖拽文件到此处或点击选择文件'
  })

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const uploadStatus = computed(() => {
    if (uploadedCount.value === 0 && !isUploading.value) {
      return ''
    }
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
      if (!isAuto) {
        passwordError.value = '请输入密码'
      }
      return false
    }

    passwordError.value = ''

    const result = await verifyUploadPassword(passwordToVerify)
    if (result.success) {
      isPasswordVerified.value = true
      password.value = passwordToVerify
      sessionStorage.setItem(PASSWORD_KEY, passwordToVerify)
      return true
    } else {
      passwordError.value = result.error || '密码错误，请重试'
      sessionStorage.removeItem(PASSWORD_KEY)
      isPasswordVerified.value = false
      return false
    }
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
    uploadedCount.value = 0
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
  }

  async function processUploadQueue(params: {
    currentPath: string
    requirePassword: boolean
    getPassword: () => string
    onWrongPassword?: () => void
    onRefresh?: () => void
  }) {
    if (uploadQueue.value.length === 0) {
      isUploading.value = false
      params.onRefresh?.()
      return
    }

    isUploading.value = true

    const file = uploadQueue.value.shift()!
    currentFileProgress.value = 0
    currentFileName.value = file.name
    currentFileSize.value = file.size
    currentFileLoaded.value = 0

    try {
      const result = await uploadFile(
        file,
        params.currentPath,
        params.requirePassword ? params.getPassword() : null,
        (progress) => {
          currentFileProgress.value = progress
          currentFileLoaded.value = (file.size * progress) / 100
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

        // 其他错误，继续处理队列
        await processUploadQueue(params)
        return
      }

      uploadedCount.value++
      currentFileProgress.value = 100

      if (result.data?.renamed) {
        renamedFiles.value.push(result.data.filename)
      }

      await processUploadQueue(params)
    } catch (err) {
      console.error('上传错误:', err)
      await processUploadQueue(params)
    }
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
    uploadedCount,
    renamedFiles,
    currentFileProgress,
    currentFileName,
    currentFileSize,
    currentFileLoaded,

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

