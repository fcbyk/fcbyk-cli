/**
 * Lansend 页面类型定义
 */

export interface DirectoryItem {
  name: string
  path: string
  is_dir: boolean
}

export interface PathPart {
  name: string
  path: string
}

export interface DirectoryData {
  require_password: boolean
  relative_path: string
  share_name: string
  path_parts: PathPart[]
  items: DirectoryItem[]
}

export interface VerifyUploadPasswordResponse {
  success: boolean
  error?: string
}

export interface PreviewFile {
  content?: string
  is_image?: boolean
  is_video?: boolean
  is_binary?: boolean
  path: string
  name: string
  error?: string
}

export interface UploadFileResponse {
  success: boolean
  data?: any
  error?: string
}

export interface ChatMessage {
  id: number
  ip: string
  message: string
  timestamp: string
}

export interface ChatMessagesResponse {
  messages: ChatMessage[]
  current_ip?: string
}

