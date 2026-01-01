import { ref } from 'vue'
import { getFileContent } from '../api'
import type { PreviewFile } from '../types'

export type LansendActiveTab = 'download' | 'upload' | 'preview' | 'empty'

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

  function closePreview(opts?: { ideMode?: boolean }) {
    previewFile.value = null
    previewError.value = ''

    // IDE 模式：关闭预览回到空白提示页
    if (opts?.ideMode) {
      activeTab.value = 'empty'
      return
    }

    const mobile = window.matchMedia('(max-width: 768px)').matches

    if (activeTab.value === 'preview') {
      activeTab.value = mobile ? 'download' : 'upload'
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
