import { ref } from 'vue'
import { getFileContent } from '../api'
import type { PreviewFile } from '../types'

function isVideoFileName(name: string) {
  const lower = (name || '').toLowerCase()
  return lower.endsWith('.mp4') || lower.endsWith('.webm') || lower.endsWith('.ogg')
}

function isVideoFile(file: Pick<PreviewFile, 'name' | 'is_video'>) {
  // 以服务端标记为准；缺失时用后缀兜底
  if (typeof file.is_video === 'boolean') return file.is_video
  return isVideoFileName(file.name)
}

export type LansendActiveTab = 'directory' | 'upload' | 'preview' | 'empty' | 'chat'

export function useLansendPreview() {
  const previewFile = ref<PreviewFile | null>(null)
  const previewLoading = ref(false)
  const previewError = ref('')
  const activeTab = ref<LansendActiveTab>('upload')

  // 视频首帧加载状态：用于解决非 fast start 的 mp4 首屏可能等待很久的问题
  // 仅影响视频预览；图片/文本依旧秒开
  const previewVideoLoading = ref(false)

  async function previewFileContent(path: string, name: string) {
    previewLoading.value = true
    previewError.value = ''
    activeTab.value = 'preview'

    // 单实例预览：点击不同文件时直接切换预览内容
    previewFile.value = {
      path,
      name
    }

    // 切换文件时先关闭视频 loading；等拿到服务端返回的 fileData 后再根据 is_video(或兜底后缀)决定是否开启
    previewVideoLoading.value = false

    try {
      const fileData = await getFileContent(path)
      previewFile.value = fileData

      if (isVideoFile(fileData)) {
        previewVideoLoading.value = true
      }
    } catch (err) {
      console.error('加载文件失败:', err)
      previewError.value = '无法加载文件内容'
      previewFile.value = {
        path,
        name,
        error: '无法加载文件内容'
      }
      previewVideoLoading.value = false
    } finally {
      previewLoading.value = false
    }
  }

  function closePreview(opts?: { unUpload?: boolean }) {
    previewFile.value = null
    previewError.value = ''
    previewVideoLoading.value = false

    const mobile = window.matchMedia('(max-width: 768px)').matches

    if (opts?.unUpload) {
      activeTab.value = mobile ? 'directory' : 'empty'
      return
    }

    if (activeTab.value === 'preview') {
      activeTab.value = mobile ? 'directory' : 'upload'
    }
  }

  function onPreviewVideoLoaded() {
    previewVideoLoading.value = false
  }

  function onPreviewVideoError() {
    // 出错也要关闭 loading，避免一直转圈
    previewVideoLoading.value = false
  }

  return {
    previewFile,
    previewLoading,
    previewError,
    activeTab,
    previewVideoLoading,
    previewFileContent,
    closePreview,
    onPreviewVideoLoaded,
    onPreviewVideoError
  }
}
