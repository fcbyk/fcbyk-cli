import { ref } from 'vue'
import { getFileContent } from '../api'
import type { PreviewFile } from '../types'

export function useLansendPreview() {
  const previewFile = ref<PreviewFile | null>(null)
  const previewLoading = ref(false)
  const previewError = ref('')
  const activeTab = ref<'download' | 'upload' | 'preview'>('upload')

  async function previewFileContent(path: string, name: string) {
    previewLoading.value = true
    previewError.value = ''
    previewFile.value = null
    activeTab.value = 'preview'

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

  function closePreview() {
    previewFile.value = null
    previewError.value = ''

    const mobile = window.matchMedia('(max-width: 768px)').matches
    
    if (mobile) {
      if (activeTab.value === 'preview') {
        activeTab.value = 'download'
      }
    }else{
      if (activeTab.value === 'preview') {
        activeTab.value = 'upload'
      }
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

