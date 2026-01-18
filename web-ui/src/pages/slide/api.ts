/**
 * Slide API 服务
 * 处理所有 HTTP 请求
 */

import type { ApiResponse, MouseMoveData, MouseScrollData } from './types'

/** 检查响应是否授权 */
async function handleResponse<T>(response: Response): Promise<T | any> {
  const data = await response.json()
  
  if (response.status === 401) {
    // 如果不是登录接口返回的 401，说明是 Session 失效，触发跳转
    if (!response.url.endsWith('/api/login')) {
      window.dispatchEvent(new CustomEvent('unauthorized'))
    }
  }
  
  return data
}

/** 检查认证状态 */
export async function checkAuth(): Promise<boolean> {
  try {
    const response = await fetch('/api/check_auth')
    const data: ApiResponse = await handleResponse(response)
    return data.authenticated ?? false
  } catch (error) {
    return false
  }
}

/** 登录 */
export async function login(password: string): Promise<ApiResponse> {
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ password })
    })
    return await handleResponse(response)
  } catch (error) {
    return {
      status: 'error',
      message: '网络错误，请重试'
    }
  }
}

/** 退出登录 */
export async function logout(): Promise<void> {
  try {
    const response = await fetch('/api/logout', { method: 'POST' })
    await handleResponse(response)
  } catch (error) {
    // 静默处理
  }
}

/** PPT 控制 - 下一页 */
export async function nextSlide(): Promise<void> {
  try {
    const response = await fetch('/api/next', { method: 'POST' })
    await handleResponse(response)
  } catch (error) {
    // 静默处理错误
  }
}

/** PPT 控制 - 上一页 */
export async function prevSlide(): Promise<void> {
  try {
    const response = await fetch('/api/prev', { method: 'POST' })
    await handleResponse(response)
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标移动 (HTTP 降级) */
export async function httpMouseMove(data: MouseMoveData): Promise<void> {
  try {
    const response = await fetch('/api/mouse/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    await handleResponse(response)
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标点击 (HTTP 降级) */
export async function httpMouseClick(): Promise<void> {
  try {
    const response = await fetch('/api/mouse/click', { method: 'POST' })
    await handleResponse(response)
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标右键 (HTTP 降级) */
export async function httpMouseRightClick(): Promise<void> {
  try {
    const response = await fetch('/api/mouse/rightclick', { method: 'POST' })
    await handleResponse(response)
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标滚动 (HTTP 降级) */
export async function httpMouseScroll(data: MouseScrollData): Promise<void> {
  try {
    const response = await fetch('/api/mouse/scroll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    await handleResponse(response)
  } catch (error) {
    // 静默处理错误
  }
}