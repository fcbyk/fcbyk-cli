/**
 * Slide WebSocket 服务
 * 处理 Socket.io 连接和事件
 */

import { io, Socket } from 'socket.io-client'

let socket: Socket | null = null

/** 初始化 WebSocket 连接 */
export function initSocket(onConnect?: () => void, onDisconnect?: () => void): Socket {
  if (socket) {
    return socket
  }

  socket = io()

  socket.on('connect', () => {
    console.log('WebSocket connected')
    onConnect?.()
  })

  socket.on('disconnect', () => {
    console.log('WebSocket disconnected')
    onDisconnect?.()
  })

  return socket
}

/** 获取 Socket 实例 */
export function getSocket(): Socket | null {
  return socket
}

/** 检查连接状态 */
export function isConnected(): boolean {
  return socket?.connected ?? false
}

/** 发送鼠标移动事件 */
export function emitMouseMove(dx: number, dy: number): void {
  if (socket && socket.connected) {
    socket.emit('mouse_move', { 
      dx: Math.round(dx), 
      dy: Math.round(dy) 
    })
  }
}

/** 发送鼠标点击事件 */
export function emitMouseClick(): void {
  if (socket && socket.connected) {
    socket.emit('mouse_click')
  }
}

/** 发送鼠标右键事件 */
export function emitMouseRightClick(): void {
  if (socket && socket.connected) {
    socket.emit('mouse_rightclick')
  }
}

/** 发送鼠标滚动事件 */
export function emitMouseScroll(dx: number, dy: number): void {
  if (socket && socket.connected) {
    socket.emit('mouse_scroll', { dx, dy })
  }
}

/** 断开连接 */
export function disconnectSocket(): void {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}