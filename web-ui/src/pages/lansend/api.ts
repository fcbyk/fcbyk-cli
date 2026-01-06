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
  onProgress: (progress: number, meta?: { loaded: number; total: number }) => void
): Promise<UploadFileResponse> {
  return new Promise((resolve, reject) => {
    // 开始上传时初始化进度
    onProgress(0, { loaded: 0, total: file.size })
    const formData = new FormData()
    formData.append('file', file)
    formData.append('path', path)
    formData.append('size', file.size.toString())
    if (password) {
      formData.append('password', password)
    }

    const xhr = new XMLHttpRequest()

    // progress 事件处理
    xhr.upload.addEventListener('progress', (e) => {
      // progress 事件处理
      const total = file.size || (e.lengthComputable && e.total > 0 ? e.total : 0)
      const loaded = Math.min(e.loaded, total || e.loaded)
      const progress = total === 0 ? 100 : (loaded / total) * 100
      onProgress(Math.min(99.9, Math.max(0, progress)), { loaded, total })
    })

    // 只有真正完成时才发 100%
    xhr.addEventListener('load', () => {
      onProgress(100, { loaded: file.size, total: file.size })
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
 * 备用接口
 * 分片上传文件（避免 4GB 单请求体触发服务端/WSGI 限制）
 */
export async function uploadFileByChunks(
  file: File,
  path: string,
  password: string | null,
  onProgress: (progress: number) => void,
  options?: {
    chunkSize?: number
    concurrency?: number
    retry?: number
    retryDelayMs?: number
  }
): Promise<UploadFileResponse> {
  const chunkSize = options?.chunkSize ?? 8 * 1024 * 1024
  const concurrency = Math.max(1, options?.concurrency ?? 3)
  const retry = Math.max(0, options?.retry ?? 2)
  const retryDelayMs = Math.max(0, options?.retryDelayMs ?? 300)

  const totalChunks = Math.max(1, Math.ceil(file.size / chunkSize))

  // init
  const initForm = new FormData()
  initForm.append('filename', file.name)
  initForm.append('size', file.size.toString())
  initForm.append('path', path)
  initForm.append('chunk_size', chunkSize.toString())
  initForm.append('total_chunks', totalChunks.toString())
  if (password) initForm.append('password', password)

  const initResp = await fetch('/api/upload/init', {
    method: 'POST',
    body: initForm,
    headers: password ? { 'X-Upload-Password': password } : undefined
  })
  const initData = await initResp.json().catch(() => ({}))
  if (!initResp.ok) {
    return { success: false, error: initData?.error || 'upload init failed', data: initData }
  }

  const uploadId: string = initData.upload_id
  if (!uploadId) {
    return { success: false, error: 'missing upload_id', data: initData }
  }

  let uploadedBytes = 0
  const chunkUploaded = new Array(totalChunks).fill(false)

  const report = () => {
    const progress = file.size === 0 ? 100 : (uploadedBytes / file.size) * 100
    onProgress(Math.min(100, Math.max(0, progress)))
  }

  async function sleep(ms: number) {
    return new Promise((r) => setTimeout(r, ms))
  }

  async function putChunk(index: number) {
    const start = index * chunkSize
    const end = Math.min(file.size, start + chunkSize)
    const blob = file.slice(start, end)

    let attempt = 0
    while (true) {
      try {
        const resp = await fetch(`/api/upload/chunk?upload_id=${encodeURIComponent(uploadId)}&index=${index}`, {
          method: 'POST',
          body: blob,
          headers: {
            'Content-Type': 'application/octet-stream',
            ...(password ? { 'X-Upload-Password': password } : {})
          }
        })
        const data = await resp.json().catch(() => ({}))
        if (!resp.ok) {
          throw new Error(data?.error || `chunk ${index} failed`)
        }

        if (!chunkUploaded[index]) {
          chunkUploaded[index] = true
          uploadedBytes += (end - start)
          report()
        }
        return
      } catch (e) {
        if (attempt >= retry) throw e
        attempt++
        await sleep(retryDelayMs)
      }
    }
  }

  // 简单并发 worker
  let nextIndex = 0
  const workers: Promise<void>[] = []
  for (let w = 0; w < concurrency; w++) {
    workers.push(
      (async () => {
        while (true) {
          const i = nextIndex
          nextIndex++
          if (i >= totalChunks) return
          await putChunk(i)
        }
      })()
    )
  }

  try {
    report()
    await Promise.all(workers)
  } catch (e: any) {
    // abort
    try {
      await fetch('/api/upload/abort', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(password ? { 'X-Upload-Password': password } : {})
        },
        body: JSON.stringify({ upload_id: uploadId })
      })
    } catch {
      // ignore
    }
    return { success: false, error: e?.message || 'upload failed' }
  }

  // complete
  const completeResp = await fetch('/api/upload/complete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(password ? { 'X-Upload-Password': password } : {})
    },
    body: JSON.stringify({ upload_id: uploadId })
  })

  const completeData = await completeResp.json().catch(() => ({}))
  if (!completeResp.ok) {
    return { success: false, error: completeData?.error || 'upload complete failed', data: completeData }
  }

  return { success: true, data: completeData }
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

