export interface User {
  id: string | number
  ip: string
  name: string
  icon: any
  x: number
  y: number
  isMe?: boolean
  isServer?: boolean
}

export interface TransferFile {
  name: string
  size: number
  type: string
  lastModified: number
}

export type TransferStatus = 'idle' | 'preparing' | 'waiting' | 'transferring' | 'completed'

export interface ReceiveRequest {
  id: string
  sender: User
  file: TransferFile
}
