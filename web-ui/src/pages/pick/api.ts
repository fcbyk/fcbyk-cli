/**
 * Pick API 服务
 */

import type { PickApiResponse, FileListApiResponse, FilePickApiResponse, FileResultApiResponse, AdminCodesApiResponse, AdminAddCodeApiResponse, InfoApiResponse } from './types'

/** 获取启动信息 */
export async function fetchInfo(): Promise<InfoApiResponse> {
  try {
    const response = await fetch('/api/info')
    const data: InfoApiResponse = await response.json()
    return data
  } catch (error) {
    console.error('Failed to fetch info:', error)
    throw new Error((error as Error).message || '获取启动信息失败')
  }
}

/** 获取候选项列表 */
export async function fetchItems(): Promise<string[]> {
  try {
    const response = await fetch('/api/items')
    const data: PickApiResponse = await response.json()
    return Array.isArray(data.items) ? data.items : []
  } catch (error) {
    console.error('Failed to fetch items:', error)
    throw new Error('加载列表失败，请稍后重试')
  }
}

/** 获取文件列表 */
export async function fetchFiles(): Promise<FileListApiResponse> {
  try {
    const response = await fetch('/api/files')
    const data: FileListApiResponse = await response.json()
    if (!response.ok) {
      throw new Error((data as any).error || '加载失败')
    }
    return data
  } catch (error) {
    console.error('Failed to fetch files:', error)
    throw new Error((error as Error).message || '加载文件列表失败，请稍后重试')
  }
}

/** 使用抽奖码抽文件 */
export async function pickFile(code: string): Promise<FilePickApiResponse> {
  try {
    const response = await fetch('/api/files/pick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    })
    const data: FilePickApiResponse = await response.json()
    if (!response.ok) {
      throw new Error((data as any).error || '抽取失败')
    }
    return data
  } catch (error) {
    console.error('Failed to pick file:', error)
    throw new Error((error as Error).message || '抽取失败')
  }
}

/** 获取抽奖结果 */
export async function getFileResult(code: string): Promise<FileResultApiResponse> {
  try {
    const response = await fetch(`/api/files/result/${encodeURIComponent(code)}`)
    if (!response.ok) {
      throw new Error('获取结果失败')
    }
    const data: FileResultApiResponse = await response.json()
    return data
  } catch (error) {
    console.error('Failed to get file result:', error)
    throw new Error((error as Error).message || '获取结果失败')
  }
}

/** 管理员登录 */
export async function adminLogin(password: string): Promise<void> {
  try {
    const response = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    })
    if (!response.ok) {
      throw new Error('密码错误')
    }
  } catch (error) {
    console.error('Failed to login:', error)
    throw new Error((error as Error).message || '登录失败')
  }
}

/** 获取兑换码列表 */
export async function fetchAdminCodes(password: string): Promise<AdminCodesApiResponse> {
  try {
    const response = await fetch('/api/admin/codes', {
      headers: { 'X-Admin-Password': password }
    })
    if (!response.ok) {
      throw new Error('获取列表失败')
    }
    const data: AdminCodesApiResponse = await response.json()
    return data
  } catch (error) {
    console.error('Failed to fetch admin codes:', error)
    throw new Error((error as Error).message || '获取列表失败')
  }
}

/** 新增兑换码 */
export async function addAdminCode(password: string, code: string): Promise<AdminAddCodeApiResponse> {
  try {
    const response = await fetch('/api/admin/codes/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Password': password
      },
      body: JSON.stringify({ code })
    })
    const data: AdminAddCodeApiResponse = await response.json()
    if (!response.ok) {
      throw new Error(data.error || '添加失败')
    }
    return data
  } catch (error) {
    console.error('Failed to add admin code:', error)
    throw new Error((error as Error).message || '添加失败')
  }
}