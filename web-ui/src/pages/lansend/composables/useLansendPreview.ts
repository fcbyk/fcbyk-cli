import { ref } from 'vue'
import { getFileContent } from '../api'
import type { PreviewFile } from '../types'

export type LansendActiveTab = 'directory' | 'upload' | 'preview' | 'empty' | 'chat'

export function useLansendPreview() {
  const previewFile = ref<PreviewFile | null>(null)
  const previewLoading = ref(false)
  const previewError = ref('')
  const activeTab = ref<LansendActiveTab>('upload')

  async function previewFileContent(path: string, name: string) {
    previewLoading.value = true
    previewError.value = ''
    activeTab.value = 'preview'

    // 单实例预览：点击不同文件时直接切换预览内容
    previewFile.value = {
      path,
      name
    }

    try {
      const fileData = await getFileContent(path)
      previewFile.value = fileData
    } catch (err) {
      console.error('加载文件失败:', err)
      previewError.value = '无法加载文件内容'
      previewFile.value = {
        path,
        name,
        error: '无法加载文件内容'
      }
    } finally {
      previewLoading.value = false
    }
  }

  function closePreview(opts?: { unUpload?: boolean }) {
    previewFile.value = null
    previewError.value = ''

    const mobile = window.matchMedia('(max-width: 768px)').matches

    if (opts?.unUpload) {
      activeTab.value = mobile ? 'directory' : 'empty'
      return
    }

    if (activeTab.value === 'preview') {
      activeTab.value = mobile ? 'directory' : 'upload'
    }
  }

  return {
    previewFile,
    previewLoading,
    previewError,
    activeTab,
    previewFileContent,
    closePreview
  }
}
