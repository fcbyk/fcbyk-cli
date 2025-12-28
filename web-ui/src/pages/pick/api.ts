/**
 * Pick API 服务
 */

import type { PickApiResponse } from './types'

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