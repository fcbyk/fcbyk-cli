/**
 * Pick 页面类型定义
 */

/** API 响应 */
export interface PickApiResponse {
    items: string[]
  }
  
  /** 状态类型 */
  export type StatusType = '' | 'ok' | 'err'
  
  /** 动画阶段配置 */
  export interface AnimationStage {
    steps: number
    delay: number
  }

  /** 文件信息 */
  export interface FileInfo {
    name: string
    size: number
  }

  /** 文件列表 API 响应 */
  export interface FileListApiResponse {
    files: FileInfo[]
    mode: 'code' | 'ip'
    used_codes?: number
    total_codes?: number
    draw_count?: number
    session_id: string
  }

  /** 文件抽奖 API 响应 */
  export interface FilePickApiResponse {
    file: FileInfo
    code: string
    download_url: string
    mode: 'code' | 'ip'
    used_codes?: number
    total_codes?: number
    draw_count?: number
  }

  /** 文件抽奖结果 API 响应 */
  export interface FileResultApiResponse {
    file: FileInfo
    download_url: string
  }

  /** 历史记录项 */
  export interface HistoryItem {
    name: string
    size: number
  }

  /** 兑换码信息 */
  export interface CodeInfo {
    code: string
    used: boolean
  }

  /** 兑换码列表 API 响应 */
  export interface AdminCodesApiResponse {
    codes: CodeInfo[]
  }

  /** 新增兑换码 API 响应 */
  export interface AdminAddCodeApiResponse {
    success?: boolean
    error?: string
  }