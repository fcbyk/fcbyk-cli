/**
 * Slide API 服务
 * 处理所有 HTTP 请求
 */

import type { ApiResponse, MouseMoveData, MouseScrollData } from './types'

/** 检查认证状态 */
export async function checkAuth(): Promise<boolean> {
  try {
    const response = await fetch('/api/check_auth')
    const data: ApiResponse = await response.json()
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
    return await response.json()
  } catch (error) {
    return {
      status: 'error',
      message: '网络错误，请重试'
    }
  }
}

/** PPT 控制 - 下一页 */
export async function nextSlide(): Promise<void> {
  try {
    await fetch('/api/next', { method: 'POST' })
  } catch (error) {
    // 静默处理错误
  }
}

/** PPT 控制 - 上一页 */
export async function prevSlide(): Promise<void> {
  try {
    await fetch('/api/prev', { method: 'POST' })
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标移动 (HTTP 降级) */
export async function httpMouseMove(data: MouseMoveData): Promise<void> {
  try {
    await fetch('/api/mouse/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标点击 (HTTP 降级) */
export async function httpMouseClick(): Promise<void> {
  try {
    await fetch('/api/mouse/click', { method: 'POST' })
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标右键 (HTTP 降级) */
export async function httpMouseRightClick(): Promise<void> {
  try {
    await fetch('/api/mouse/rightclick', { method: 'POST' })
  } catch (error) {
    // 静默处理错误
  }
}

/** 鼠标滚动 (HTTP 降级) */
export async function httpMouseScroll(data: MouseScrollData): Promise<void> {
  try {
    await fetch('/api/mouse/scroll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
  } catch (error) {
    // 静默处理错误
  }
}