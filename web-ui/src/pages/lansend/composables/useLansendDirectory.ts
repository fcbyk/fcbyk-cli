import { ref } from 'vue'
import { getDirectory } from '../api'
import type { DirectoryItem, PathPart } from '../types'

const PATH_KEY = 'lansendCurrentPath'

export function useLansendDirectory() {
  const displayName = ref('加载中...')
  const shareName = ref('')
  const pathParts = ref<PathPart[]>([])
  const items = ref<DirectoryItem[]>([])
  const loading = ref(true)
  const error = ref('')
  const requirePassword = ref(false)
  const currentPath = ref('')

  async function loadDirectory(path: string = '') {
    loading.value = true
    error.value = ''
    currentPath.value = path

    try {
      const data = await getDirectory(path)
      displayName.value = data.display_name
      requirePassword.value = data.require_password
      currentPath.value = data.relative_path
      shareName.value = data.share_name
      pathParts.value = data.path_parts || []
      items.value = data.items || []

      // 保存当前路径到会话存储
      sessionStorage.setItem(PATH_KEY, data.relative_path || '')

      return data
    } catch (err) {
      console.error('加载目录失败:', err)
      error.value = '加载失败，请刷新页面重试'
      displayName.value = '加载失败'
      return null
    } finally {
      loading.value = false
    }
  }

  function restorePathFromSession() {
    const savedPath = sessionStorage.getItem(PATH_KEY)
    return savedPath !== null ? savedPath : ''
  }

  return {
    displayName,
    shareName,
    pathParts,
    items,
    loading,
    error,
    requirePassword,
    currentPath,
    loadDirectory,
    restorePathFromSession
  }
}

