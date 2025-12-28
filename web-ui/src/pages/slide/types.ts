/**
 * Slide 页面类型定义
 */

/** API 响应基础类型 */
export interface ApiResponse {
    status: 'success' | 'error'
    message?: string
    authenticated?: boolean
    action?: string
  }
  
  /** 鼠标移动数据 */
  export interface MouseMoveData {
    dx: number
    dy: number
  }
  
  /** 鼠标滚动数据 */
  export interface MouseScrollData {
    dx: number
    dy: number
  }
  
  /** 触摸状态 */
  export interface TouchState {
    count: number
    startTime: number
    isMoving: boolean
    twoFingerMoved: boolean
    lastX: number
    lastY: number
    lastTwoFingerY: number
    moveAccumulator: {
      dx: number
      dy: number
    }
    rafId: number | null
  }
  
  /** WebSocket 连接状态 */
  export interface SocketState {
    connected: boolean
    instance: any | null
  }