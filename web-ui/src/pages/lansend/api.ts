import type {
  DirectoryData,
  VerifyUploadPasswordResponse,
  PreviewFile,
  UploadFileResponse,
  ChatMessage,
  ChatMessagesResponse
} from './types'

/**
 * 获取目录数据
 */
export async function getDirectory(path: string = ''): Promise<DirectoryData> {
  const response = await fetch(`/api/directory?path=${encodeURIComponent(path)}`)
  if (!response.ok) {
    throw new Error('Failed to load directory')
  }
  return await response.json()
}

/**
 * 验证上传密码
 */
export async function verifyUploadPassword(password: string): Promise<VerifyUploadPasswordResponse> {
  try {
    const response = await fetch('/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `password=${encodeURIComponent(password)}`
    })

    const data = await response.json()

    if (!response.ok || (data && data.error === 'wrong password')) {
      return { success: false, error: '密码错误，请重试' }
    }

    if (data && data.error) {
      return { success: false, error: data.error }
    }

    return { success: true }
  } catch (error) {
    console.error('验证错误:', error)
    return { success: false, error: '验证失败，请重试' }
  }
}

/**
 * 获取文件内容（用于预览）
 */
export async function getFileContent(path: string): Promise<PreviewFile> {
  const response = await fetch(`/api/file/${encodeURIComponent(path)}`)
  if (!response.ok) {
    throw new Error('Failed to load file')
  }
  return await response.json()
}

/**
 * 上传文件
 */
export function uploadFile(
  file: File,
  path: string,
  password: string | null,
  onProgress: (progress: number) => void
): Promise<UploadFileResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('path', path)
    formData.append('size', file.size.toString())
    if (password) {
      formData.append('password', password)
    }

    const xhr = new XMLHttpRequest()

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const progress = (e.loaded / e.total) * 100
        onProgress(progress)
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        try {
          const data = JSON.parse(xhr.responseText)
          if (data.error) {
            resolve({ success: false, error: data.error, data })
          } else {
            resolve({ success: true, data })
          }
        } catch (error) {
          reject(new Error('解析响应错误'))
        }
      } else {
        reject(new Error(`上传错误: ${xhr.status} ${xhr.statusText}`))
      }
    })

    xhr.addEventListener('error', () => {
      reject(new Error('上传错误'))
    })

    xhr.open('POST', '/upload')
    xhr.send(formData)
  })
}

/**
 * 获取聊天消息列表
 */
export async function getChatMessages(): Promise<ChatMessagesResponse> {
  const response = await fetch('/api/chat/messages')
  if (!response.ok) {
    throw new Error('Failed to load chat messages')
  }
  return await response.json()
}

/**
 * 发送聊天消息
 */
export async function sendChatMessage(message: string): Promise<{ success: boolean; message: ChatMessage }> {
  const response = await fetch('/api/chat/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  })
  if (!response.ok) {
    throw new Error('Failed to send message')
  }
  return await response.json()
}

