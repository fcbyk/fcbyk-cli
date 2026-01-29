import { ref, onMounted, onUnmounted, computed } from 'vue'
import { 
  Smartphone, 
  Laptop, 
  Tablet, 
  Tv, 
  Watch, 
  HardDrive,
  Monitor as MonitorIcon
} from 'lucide-vue-next'
import type { User, TransferFile, TransferStatus, ReceiveRequest } from '../types'
import {
  pingServer,
  getOnlineUsers,
  requestTransfer,
  getTransferStatus,
  respondTransfer,
  pushFileStream,
  cancelTransferTask,
  API_BASE,
  getTransferSession
} from '../api'

export function useTransfer() {
  const icons: Record<string, any> = {
    Smartphone, Laptop, Tablet, Tv, Watch, HardDrive
  }
  const users = ref<User[]>([])
  const myIp = ref('')
  const isServer = ref(false)

  // 发送相关状态
  const activeTargetId = ref<string | number | null>(null) // -1 代表中心服务器
  const transferStatus = ref<TransferStatus>('idle')
  const selectedFile = ref<TransferFile | null>(null)
  const nativeFile = ref<File | null>(null)
  const currentTaskId = ref<string | null>(null)
  
  // 接收相关状态
  const receiveRequest = ref<ReceiveRequest | null>(null)
  const isReceivePreparing = ref(false)
  const isReceiving = ref(false)

  // 公共状态
  const progress = ref(0)
  let statusTimer: number | null = null
  let progressTimer: number | null = null
  let pollTimer: number | null = null

  const activeTransfer = computed(() => transferStatus.value === 'transferring')
  const isWaiting = computed(() => transferStatus.value === 'waiting')
  const isPreparing = computed(() => transferStatus.value === 'preparing')
  const isServerTarget = computed(() => activeTargetId.value === -1)
  const me = computed(() => users.value.find(u => u.isMe))
  
  const activeTarget = computed(() => {
    if (activeTargetId.value === -1) {
      return { id: -1, name: '中心服务器', x: 0, y: 0, ip: serverHost, icon: MonitorIcon } as User
    }
    return users.value.find(u => u.id === activeTargetId.value)
  })

  const sender = computed(() => {
    return me.value
  })

  const serverHost = window.location.hostname

  // 缓存用户位置，确保同一次页面加载内位置固定，但刷新后随机
  const userPositions = new Map<string | number, { x: number, y: number }>()

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
  }

  // 定位计算工具 (随机分布)
  const getRandomPosition = (userId: string | number) => {
    // 如果已经分配过位置，直接返回
    if (userPositions.has(userId)) {
      return userPositions.get(userId)!
    }

    const safePadding = 120
    const minDistance = 160
    const serverSafeRadius = 180
    
    const rangeX = (windowSize.value.width / 2) - safePadding
    const rangeY = (windowSize.value.height / 2) - safePadding

    let x = 0, y = 0
    let attempts = 0
    let isValid = false

    while (!isValid && attempts < 100) {
      attempts++
      // 在屏幕范围内随机
      x = (Math.random() * 2 - 1) * rangeX
      y = (Math.random() * 2 - 1) * rangeY

      // 1. 避开中心服务器
      const distToServer = Math.sqrt(x * x + y * y)
      if (distToServer < serverSafeRadius) continue

      // 2. 避开已有的其他用户节点
      let overlapping = false
      for (const pos of userPositions.values()) {
        const dx = x - pos.x
        const dy = y - pos.y
        if (Math.sqrt(dx * dx + dy * dy) < minDistance) {
          overlapping = true
          break
        }
      }
      
      if (!overlapping) isValid = true
    }

    const pos = { x, y }
    userPositions.set(userId, pos)
    return pos
  }

  // 轮询逻辑
  const startPolling = () => {
    const poll = async () => {
      try {
        // 1. 心跳上报并检查请求
        const pingData = await pingServer({
          name: `Device-${window.navigator.platform}`,
          icon: 'Laptop',
          isMe: true
        })
        myIp.value = pingData.ip
        isServer.value = pingData.is_server

        if (pingData.pending_request && !receiveRequest.value && !activeTransfer.value) {
          const pending = pingData.pending_request as any
          if (pending.sender) {
            const iconKey = pending.sender.icon || 'Laptop'
            pending.sender = {
              ...pending.sender,
              icon: icons[iconKey] || Smartphone
            }
          }
          receiveRequest.value = pending
        }

        // 2. 获取所有在线用户
        const onlineUsers = await getOnlineUsers()
        
        // 3. 映射到带坐标的 User 对象
        // 过滤掉所有被标记为服务器的节点（因为它们由中心图标表示）
        // 但是要小心：如果当前用户被误识别为服务器，但他其实是想作为普通用户显示（例如在手机上通过代理访问）
        const otherUsers = onlineUsers.filter(u => {
          // 如果是服务器节点，且不是“我自己”（或者即使是我自己，只要它是服务器角色就由中心节点代表）
          if (u.isServer) return false
          // 过滤掉我自己（因为如果是普通用户，我自己会显示在卫星节点中，标记为 isMe）
          // Wait, if I'm a normal user, I WANT to see myself in the satellite nodes.
          return true
        })
        
        const updatedUsers: User[] = []
        
        otherUsers.forEach((u) => {
          const pos = getRandomPosition(u.ip)
          const isActuallyMe = u.ip === myIp.value
          
          updatedUsers.push({
            ...u,
            id: u.ip,
            icon: icons[u.icon] || Smartphone,
            x: pos.x,
            y: pos.y,
            isMe: isActuallyMe
          })
        })
        
        users.value = updatedUsers
      } catch (e) {
        console.error('Polling failed:', e)
      }
    }

    poll()
    pollTimer = window.setInterval(poll, 3000)
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
    nativeFile.value = null
  }

  const handleServerClick = () => {
    if (isServer.value && receiveRequest.value) {
      isReceivePreparing.value = true
      return
    }
    if (transferStatus.value !== 'idle' && activeTargetId.value === -1) return
    
    activeTargetId.value = -1
    transferStatus.value = 'preparing'
    selectedFile.value = null
    nativeFile.value = null
  }

  const cancelTransfer = async () => {
    if (currentTaskId.value) {
      await cancelTransferTask(currentTaskId.value)
    }
    
    activeTargetId.value = null
    transferStatus.value = 'idle'
    selectedFile.value = null
    nativeFile.value = null
    isReceiving.value = false
    isReceivePreparing.value = false
    progress.value = 0
    currentTaskId.value = null
    if (statusTimer) {
      clearInterval(statusTimer)
      statusTimer = null
    }
    if (progressTimer) {
      clearInterval(progressTimer)
      progressTimer = null
    }
  }

  const acceptReceive = async () => {
    if (!receiveRequest.value) return
    const taskId = receiveRequest.value.id
    const file = receiveRequest.value.file
    const fileName = file.name
    
    try {
      await respondTransfer(taskId, true)
      isReceiving.value = true
      currentTaskId.value = taskId
      selectedFile.value = file
      progress.value = 0

      const downloadUrl = `${API_BASE}/api/transfer/pull/${taskId}`
      const link = document.createElement('a')
      link.href = downloadUrl
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      const pollProgress = async () => {
        if (!currentTaskId.value) return
        try {
          const session = await getTransferSession(currentTaskId.value)
          const total = session.total_size || file.size || 0
          if (total > 0) {
            const p = Math.round((session.received_bytes / total) * 100)
            progress.value = Math.min(100, Math.max(0, p))
          }
          if (session.state === 'completed' || session.state === 'failed') {
            if (progressTimer) {
              clearInterval(progressTimer)
              progressTimer = null
            }
            if (session.state === 'completed') {
              completeTransfer()
            } else {
              cancelTransfer()
            }
          }
        } catch (e) {
          console.error('Progress poll failed:', e)
        }
      }

      if (progressTimer) {
        clearInterval(progressTimer)
        progressTimer = null
      }
      pollProgress()
      progressTimer = window.setInterval(pollProgress, 1000)

      isReceivePreparing.value = false
      receiveRequest.value = null
    } catch (e) {
      console.error('Accept failed:', e)
      alert('接受失败: ' + e)
    }
  }

  const rejectReceive = async () => {
    if (!receiveRequest.value) return
    try {
      await respondTransfer(receiveRequest.value.id, false)
    } catch (e) {
      console.error('Reject failed:', e)
    }
    receiveRequest.value = null
    isReceivePreparing.value = false
  }
  
  const closeReceivePanel = () => {
    isReceivePreparing.value = false
  }

  const handleFileSelect = (file: File) => {
    nativeFile.value = file
    selectedFile.value = {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified
    }
  }

  const startTransfer = async () => {
    if (!selectedFile.value || !nativeFile.value || activeTargetId.value === null) return
    
    try {
      const receiverIp = activeTargetId.value === -1 ? 'SERVER' : String(activeTargetId.value)
      const taskId = await requestTransfer(receiverIp, selectedFile.value)
      currentTaskId.value = taskId
      transferStatus.value = 'waiting'
      
      let waitCount = 0

      const checkStatus = async () => {
        const status = await getTransferStatus(taskId)
        if (status === 'accepted') {
          if (statusTimer) {
            clearInterval(statusTimer)
            statusTimer = null
          }

          transferStatus.value = 'transferring'
          startProgress()

          const pollSession = async () => {
            try {
              const session = await getTransferSession(taskId)
              const total = session.total_size || selectedFile.value?.size || 0
              if (total && session.sent_bytes >= 0) {
                const percent = Math.round((session.sent_bytes / total) * 100)
                if (percent > progress.value) {
                  progress.value = Math.min(100, percent)
                }
              }
              if (session.state === 'completed' || session.state === 'failed') {
                if (statusTimer) {
                  clearInterval(statusTimer)
                  statusTimer = null
                }
                if (session.state === 'completed') {
                  completeTransfer()
                } else {
                  cancelTransfer()
                }
              }
            } catch (e) {
              console.error('Session poll failed:', e)
            }
          }

          pushFileStream(taskId, nativeFile.value!, (p) => {
            progress.value = p
          }).catch((e) => {
            console.error('Push failed:', e)
            alert('推送失败: ' + e)
            cancelTransfer()
          })

          pollSession()
          statusTimer = window.setInterval(pollSession, 1000)
        } else if (status === 'rejected' || status === 'cancelled') {
          if (statusTimer) {
            clearInterval(statusTimer)
            statusTimer = null
          }
          alert('传输被拒绝或取消')
          cancelTransfer()
        } else {
          waitCount++
          if (waitCount > 20) {
            if (statusTimer) {
              clearInterval(statusTimer)
              statusTimer = null
            }
            alert('等待超时')
            cancelTransfer()
          }
        }
      }
      
      statusTimer = window.setInterval(checkStatus, 3000)
    } catch (e) {
      console.error('Transfer failed:', e)
      alert('传输失败: ' + e)
      cancelTransfer()
    }
  }

  const startProgress = () => {
    // 弃用模拟进度，现在由 pushFileStream 真实更新
    progress.value = 0
  }

  const completeTransfer = () => {
    progress.value = 100
    transferStatus.value = 'completed'
    
    setTimeout(() => {
      if (transferStatus.value === 'completed') {
        cancelTransfer()
      }
    }, 3000)
  }

  onMounted(() => {
    window.addEventListener('resize', updateWindowSize)
    startPolling()
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateWindowSize)
    if (statusTimer) clearInterval(statusTimer)
    if (progressTimer) clearInterval(progressTimer)
    if (pollTimer) clearInterval(pollTimer)
  })

  return {
    users,
    isServer,
    activeTargetId,
    transferStatus,
    selectedFile,
    receiveRequest,
    isReceivePreparing,
    isReceiving,
    progress,
    activeTransfer,
    isWaiting,
    isPreparing,
    isServerTarget,
    me,
    activeTarget,
    sender,
    windowSize,
    serverHost,
    handleUserClick,
    handleServerClick,
    handleFileSelect,
    startTransfer,
    cancelTransfer,
    acceptReceive,
    rejectReceive,
    closeReceivePanel
  }
}
