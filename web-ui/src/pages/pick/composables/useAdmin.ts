/**
 * 管理员功能组合式函数
 */

import { ref, computed } from 'vue'
import { adminLogin, fetchAdminCodes, addAdminCode } from '../api'
import type { CodeInfo } from '../types'

const KEY_AUTH = 'admin_authed'
const KEY_PW = 'admin_pw'

export function useAdmin() {
  // 登录状态
  const password = ref('')
  const loginError = ref('')
  const isAuthenticated = ref(false)
  const adminPw = ref('')

  // 兑换码列表
  const codes = ref<CodeInfo[]>([])
  const revealedCodes = ref(new Set<string>())
  const copiedCode = ref('')

  // 新增兑换码
  const newCode = ref('')
  const addCodeMsg = ref('')
  const addCodeMsgType = ref<'success' | 'error' | ''>('')

  // 统计信息
  const stats = computed(() => {
    const total = codes.value.length
    const used = codes.value.filter(c => c.used).length
    return {
      total,
      used,
      left: total - used
    }
  })

  // 遮罩兑换码
  function maskCode(code: string): string {
    return '████████'.slice(0, code.length)
  }

  // 登录
  async function handleLogin() {
    if (!password.value) {
      loginError.value = '请输入密码'
      return
    }

    try {
      await adminLogin(password.value)
      sessionStorage.setItem(KEY_AUTH, '1')
      sessionStorage.setItem(KEY_PW, password.value)
      adminPw.value = password.value
      isAuthenticated.value = true
      loginError.value = ''
      await loadCodes()
    } catch (error) {
      loginError.value = (error as Error).message
    }
  }

  // 加载兑换码列表
  async function loadCodes() {
    try {
      const data = await fetchAdminCodes(adminPw.value)
      codes.value = data.codes
    } catch (error) {
      console.error('Failed to load codes:', error)
    }
  }

  // 切换显示/隐藏兑换码
  function toggleReveal(code: string) {
    if (revealedCodes.value.has(code)) {
      revealedCodes.value.delete(code)
    } else {
      revealedCodes.value.add(code)
    }
  }

  // 复制兑换码
  async function copyCode(code: string) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(code)
      } else {
        const textarea = document.createElement('textarea')
        textarea.value = code
        textarea.style.position = 'fixed'
        textarea.style.opacity = '0'
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
      }
      copiedCode.value = code
      setTimeout(() => {
        copiedCode.value = ''
      }, 800)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  // 新增兑换码
  async function handleAddCode() {
    const code = newCode.value.trim().toUpperCase()

    if (!code) {
      addCodeMsg.value = '请输入兑换码'
      addCodeMsgType.value = 'error'
      return
    }

    // 验证格式：只允许字母和数字
    if (!/^[A-Z0-9]+$/.test(code)) {
      addCodeMsg.value = '兑换码只能包含字母和数字'
      addCodeMsgType.value = 'error'
      return
    }

    try {
      const data = await addAdminCode(adminPw.value, code)
      if (data.error) {
        addCodeMsg.value = data.error
        addCodeMsgType.value = 'error'
      } else {
        addCodeMsg.value = `成功新增兑换码: ${code}`
        addCodeMsgType.value = 'success'
        newCode.value = ''
        await loadCodes()
        setTimeout(() => {
          addCodeMsg.value = ''
          addCodeMsgType.value = ''
        }, 2000)
      }
    } catch (error) {
      addCodeMsg.value = '添加失败: ' + (error as Error).message
      addCodeMsgType.value = 'error'
    }
  }

  // 检查兑换码是否已显示
  function isCodeRevealed(code: string): boolean {
    return revealedCodes.value.has(code)
  }

  // 检查兑换码是否已复制
  function isCodeCopied(code: string): boolean {
    return copiedCode.value === code
  }

  // 初始化（自动恢复登录状态）
  function init() {
    if (sessionStorage.getItem(KEY_AUTH) === '1') {
      adminPw.value = sessionStorage.getItem(KEY_PW) || ''
      if (adminPw.value) {
        isAuthenticated.value = true
        loadCodes()
      }
    }
  }

  return {
    // 登录状态
    password,
    loginError,
    isAuthenticated,
    
    // 兑换码列表
    codes,
    revealedCodes,
    copiedCode,
    
    // 新增兑换码
    newCode,
    addCodeMsg,
    addCodeMsgType,
    
    // 计算属性
    stats,
    
    // 方法
    maskCode,
    handleLogin,
    loadCodes,
    toggleReveal,
    copyCode,
    handleAddCode,
    isCodeRevealed,
    isCodeCopied,
    init
  }
}
