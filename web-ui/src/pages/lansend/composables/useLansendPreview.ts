import { ref } from 'vue'
import { getFileContent } from '../api'
import type { PreviewFile } from '../types'

function isVideoFileName(name: string) {
  const lower = (name || '').toLowerCase()
  return lower.endsWith('.mp4') || lower.endsWith('.webm') || lower.endsWith('.ogg')
}

function isVideoFile(file: Pick<PreviewFile, 'name' | 'is_video'>) {
  if (typeof file.is_video === 'boolean') return file.is_video
  return isVideoFileName(file.name)
}

export type LansendActiveTab = 'directory' | 'preview' | 'empty' | 'chat' | 'upload-details'

export function useLansendPreview() {
  const previewFile = ref<PreviewFile | null>(null)
  const previewLoading = ref(false)
  const previewError = ref('')
  const activeTab = ref<LansendActiveTab>('empty')

  const previewVideoLoading = ref(false)

  async function previewFileContent(path: string, name: string) {
    previewLoading.value = true
    previewError.value = ''
    activeTab.value = 'preview'

    previewFile.value = {
      path,
      name
    }

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
      activeTab.value = mobile ? 'directory' : 'empty'
    }
  }

  function onPreviewVideoLoaded() {
    previewVideoLoading.value = false
  }

  function onPreviewVideoError() {
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
