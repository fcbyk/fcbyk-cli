import { ref, onMounted, onUnmounted, computed } from 'vue'
import { 
  Smartphone, 
  Laptop, 
  Tablet, 
  Tv, 
  Watch, 
  HardDrive 
} from 'lucide-vue-next'
import type { User, TransferFile, TransferStatus, ReceiveRequest } from '../types'

export function useTransfer() {
  const icons = [Smartphone, Laptop, Tablet, Tv, Watch, HardDrive]
  const users = ref<User[]>([])

  // 发送相关状态
  const activeTargetId = ref<number | null>(null) // -1 代表中心服务器
  const transferStatus = ref<TransferStatus>('idle')
  const selectedFile = ref<TransferFile | null>(null)
  
  // 接收相关状态
  const receiveRequest = ref<ReceiveRequest | null>(null)
  const isReceiving = ref(false)
  const isReceivePreparing = ref(false)

  // 公共状态
  const countdown = ref(0)
  const progress = ref(0)
  let timer: number | null = null

  const activeTransfer = computed(() => transferStatus.value === 'transferring' || isReceiving.value)
  const isPreparing = computed(() => transferStatus.value === 'preparing')
  const isServerTarget = computed(() => activeTargetId.value === -1)
  const me = computed(() => users.value.find(u => u.isMe))
  
  const activeTarget = computed(() => {
    if (isReceiving.value && receiveRequest.value) {
      return me.value // 接收时，目标是我自己
    }
    if (activeTargetId.value === -1) {
      return { id: -1, name: '中心服务器', x: 0, y: 0 }
    }
    return users.value.find(u => u.id === activeTargetId.value)
  })

  const sender = computed(() => {
    if (isReceiving.value && receiveRequest.value) {
      return receiveRequest.value.sender
    }
    return me.value
  })

  // 窗口尺寸
  const windowSize = ref({
    width: window.innerWidth,
    height: window.innerHeight
  })

  const updateWindowSize = () => {
    windowSize.value = {
      width: window.innerWidth,
      height: window.innerHeight
    }
    generateUsers()
  }

  // 发送逻辑
  const handleUserClick = (user: User) => {
    if (user.isMe) {
      if (receiveRequest.value) {
        isReceivePreparing.value = true
      }
      return
    }
    if (transferStatus.value !== 'idle' && activeTargetId.value === user.id) return
    
    activeTargetId.value = user.id
    transferStatus.value = 'preparing'
    selectedFile.value = null
  }

  const handleServerClick = () => {
    if (transferStatus.value !== 'idle' && activeTargetId.value === -1) return
    
    activeTargetId.value = -1
    transferStatus.value = 'preparing'
    selectedFile.value = null
  }

  const cancelTransfer = () => {
    activeTargetId.value = null
    transferStatus.value = 'idle'
    selectedFile.value = null
    isReceiving.value = false
    isReceivePreparing.value = false
    progress.value = 0
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  // 接收逻辑
  const acceptReceive = () => {
    if (!receiveRequest.value) return
    isReceivePreparing.value = false
    isReceiving.value = true
    startProgress()
  }

  const rejectReceive = () => {
    receiveRequest.value = null
    isReceivePreparing.value = false
  }

  // 模拟收到文件请求
  const simulateIncomingFile = () => {
    const otherUsers = users.value.filter(u => !u.isMe)
    if (otherUsers.length === 0) return
    
    const randomSender = otherUsers[Math.floor(Math.random() * otherUsers.length)]
    receiveRequest.value = {
      id: Math.random().toString(36).substring(7),
      sender: randomSender,
      file: {
        name: 'Project_Design_Final.zip',
        size: 1024 * 1024 * 45.5, // 45.5 MB
        type: 'application/zip',
        lastModified: Date.now()
      }
    }
  }

  const handleFileSelect = (file: File) => {
    selectedFile.value = {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified
    }
  }

  const startTransfer = () => {
    if (!selectedFile.value || activeTargetId.value === null) return
    transferStatus.value = 'transferring'
    startProgress()
  }

  const startProgress = () => {
    progress.value = 0
    if (timer) clearInterval(timer)
    
    timer = window.setInterval(() => {
      progress.value += 10
      if (progress.value >= 100) {
        completeTransfer()
      }
    }, 400)
  }

  const completeTransfer = () => {
    if (isReceiving.value) {
      isReceiving.value = false
      receiveRequest.value = null
    }
    transferStatus.value = 'completed'
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    setTimeout(() => {
      if (transferStatus.value === 'completed') {
        cancelTransfer()
      }
    }, 3000)
  }

  const generateUsers = () => {
    const userCount = 3
    const newUsers: User[] = []
    const safePadding = 120
    const minDistance = 160
    const serverSafeRadius = 180
    
    const rangeX = (windowSize.value.width / 2) - safePadding
    const rangeY = (windowSize.value.height / 2) - safePadding

    for (let i = 0; i < userCount; i++) {
      let x = 0, y = 0
      let attempts = 0
      let isValid = false

      while (!isValid && attempts < 100) {
        attempts++
        x = (Math.random() * 2 - 1) * rangeX
        y = (Math.random() * 2 - 1) * rangeY

        const distToServer = Math.sqrt(x * x + y * y)
        if (distToServer < serverSafeRadius) continue

        let overlapping = false
        for (const other of newUsers) {
          const dx = x - other.x
          const dy = y - other.y
          if (Math.sqrt(dx * dx + dy * dy) < minDistance) {
            overlapping = true
            break
          }
        }
        
        if (!overlapping) isValid = true
      }

      newUsers.push({
        id: i,
        name: i === 0 ? 'Device-U5ZE' : `Device-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
        icon: icons[Math.floor(Math.random() * icons.length)],
        x,
        y,
        isMe: i === 0
      })
    }
    users.value = newUsers
  }

  onMounted(() => {
    window.addEventListener('resize', updateWindowSize)
    generateUsers()
    
    // 5秒后模拟收到一个文件
    setTimeout(simulateIncomingFile, 5000)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateWindowSize)
    if (timer) clearInterval(timer)
  })

  return {
    users,
    activeTargetId,
    transferStatus,
    selectedFile,
    receiveRequest,
    isReceiving,
    isReceivePreparing,
    progress,
    activeTransfer,
    isPreparing,
    isServerTarget,
    me,
    activeTarget,
    sender,
    windowSize,
    handleUserClick,
    handleServerClick,
    handleFileSelect,
    startTransfer,
    cancelTransfer,
    acceptReceive,
    rejectReceive,
    generateUsers
  }
}
