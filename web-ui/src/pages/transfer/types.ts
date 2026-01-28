export interface User {
  id: number
  name: string
  icon: any
  x: number
  y: number
  isMe?: boolean
}

export interface TransferFile {
  name: string
  size: number
  type: string
  lastModified: number
}

export type TransferStatus = 'idle' | 'preparing' | 'transferring' | 'completed'

export interface ReceiveRequest {
  id: string
  sender: User
  file: TransferFile
}
