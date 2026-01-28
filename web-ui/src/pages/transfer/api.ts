import type { User, TransferFile, ReceiveRequest } from './types'

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PingResponse {
  ip: string
  is_server: boolean
  pending_request: ReceiveRequest | null
}

export const API_BASE = window.location.port === '5173' ? `${window.location.protocol}//${window.location.hostname}:80` : ''

/**
 * 客户端心跳上报
 */
export async function pingServer(data: { name: string, icon: string, isMe: boolean }): Promise<PingResponse> {
  const response = await fetch(`${API_BASE}/api/transfer/ping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  const result: ApiResponse<PingResponse> = await response.json()
  if (result.code !== 200) throw new Error(result.message)
  return result.data
}

/**
 * 获取在线用户列表
 */
export async function getOnlineUsers(): Promise<User[]> {
  const response = await fetch(`${API_BASE}/api/transfer/users`)
  const result: ApiResponse<User[]> = await response.json()
  if (result.code !== 200) throw new Error(result.message)
  return result.data
}

/**
 * 发起传输请求
 */
export async function requestTransfer(receiverIp: string, file: TransferFile): Promise<string> {
  const response = await fetch(`${API_BASE}/api/transfer/request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ receiverIp, file })
  })
  const result: ApiResponse<{ taskId: string }> = await response.json()
  if (result.code !== 200) throw new Error(result.message)
  return result.data.taskId
}

/**
 * 回复传输请求
 */
export async function respondTransfer(taskId: string, accepted: boolean): Promise<void> {
  const response = await fetch(`${API_BASE}/api/transfer/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ taskId, accepted })
  })
  const result: ApiResponse = await response.json()
  if (result.code !== 200) throw new Error(result.message)
}

/**
 * 获取传输状态
 */
export async function getTransferStatus(taskId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/transfer/status/${taskId}`)
  const result: ApiResponse<{ status: string }> = await response.json()
  if (result.code !== 200) throw new Error(result.message)
  return result.data.status
}

/**
 * 推送文件流并追踪进度
 */
export async function pushFileStream(
  taskId: string, 
  file: File, 
  onProgress?: (percent: number) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100)
        onProgress(percent)
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const result: ApiResponse = JSON.parse(xhr.responseText)
          if (result.code === 200) {
            resolve()
          } else {
            reject(new Error(result.message))
          }
        } catch (e) {
          resolve() // 即使解析 JSON 失败，只要状态码 OK 也认为成功
        }
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`))
      }
    })

    xhr.addEventListener('error', () => reject(new Error('Network error')))
    xhr.addEventListener('abort', () => reject(new Error('Upload aborted')))

    xhr.open('POST', `${API_BASE}/api/transfer/push/${taskId}`)
    xhr.send(file)
  })
}

/**
 * 取消传输
 */
export async function cancelTransferTask(taskId: string): Promise<void> {
  await fetch(`${API_BASE}/api/transfer/cancel/${taskId}`, { method: 'POST' })
}
