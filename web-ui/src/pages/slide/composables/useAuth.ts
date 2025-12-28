/**
 * 认证逻辑组合式函数
 */

import { ref, onMounted } from 'vue'
import { checkAuth, login as apiLogin } from '../api'

export function useAuth() {
  const isAuthenticated = ref(false)
  const isLoading = ref(false)
  const errorMessage = ref('')

  /** 检查认证状态 */
  async function checkAuthStatus() {
    const authenticated = await checkAuth()
    if (authenticated) {
      isAuthenticated.value = true
    }
  }

  /** 登录 */
  async function login(password: string) {
    if (!password.trim()) {
      errorMessage.value = '请输入密码'
      return false
    }

    isLoading.value = true
    errorMessage.value = ''

    try {
      const result = await apiLogin(password)

      if (result.status === 'success') {
        isAuthenticated.value = true
        return true
      } else {
        errorMessage.value = result.message || '登录失败'
        return false
      }
    } catch (error) {
      errorMessage.value = '网络错误，请重试'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /** 清除错误信息 */
  function clearError() {
    errorMessage.value = ''
  }

  // 组件挂载时检查认证状态
  onMounted(() => {
    checkAuthStatus()
  })

  return {
    isAuthenticated,
    isLoading,
    errorMessage,
    login,
    clearError
  }
}