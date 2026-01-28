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
  API_BASE
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
          receiveRequest.value = pingData.pending_request
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

  // 接收逻辑
  const acceptReceive = async () => {
    if (!receiveRequest.value) return
    const taskId = receiveRequest.value.id
    const fileName = receiveRequest.value.file.name
    
    try {
      await respondTransfer(taskId, true)
      isReceiving.value = true
      
      // 使用 a 标签触发下载，这在移动端兼容性更好，且能更好地触发“保存到文件”
      const downloadUrl = `${API_BASE}/api/transfer/pull/${taskId}`
      const link = document.createElement('a')
      link.href = downloadUrl
      // 提示：download 属性在跨域时可能无效，但由于我们是同源或配置了 CORS，通常没问题
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // 重置接收状态
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
      // 1. 如果目标是服务器，走普通上传逻辑
      const receiverIp = activeTargetId.value === -1 ? 'SERVER' : String(activeTargetId.value)
      
      // 2. 发起请求
      const taskId = await requestTransfer(receiverIp, selectedFile.value)
      currentTaskId.value = taskId
      transferStatus.value = 'waiting'
      
      // 3. 等待对方接受 (轮询状态)
      let waitCount = 0
      
      // 如果目标是服务器，服务器在后端已经自动 accepted 了，
      // 我们这里也可以直接触发 checkStatus，或者缩短第一次轮询时间
      
      const checkStatus = async () => {
        const status = await getTransferStatus(taskId)
        if (status === 'accepted') {
          if (statusTimer) {
            clearInterval(statusTimer)
            statusTimer = null
          }
          // 4. 开始推送流
          transferStatus.value = 'transferring'
          startProgress() // UI 进度
          try {
            // 如果是发给服务器，推送完成后，后端需要有一个地方来消耗这个流（保存到磁盘）
            // 我们在后端添加了一个 /api/transfer/server/receive/<taskId> 接口
            // 这里我们用“并发”方式通知服务器开始接收，或者后端在 push 结束时自动触发。
            // 为了简单起见，我们在前端 push 的同时，如果是发给服务器，就触发一次服务器接收。
            if (receiverIp === 'SERVER') {
              fetch(`${API_BASE}/api/transfer/server/receive/${taskId}`).catch(console.error)
            }

            // 这里的 pushFileStream 现在会通过回调更新真实的 progress.value
            await pushFileStream(taskId, nativeFile.value!, (p) => {
              progress.value = p
            })
            
            // 数据推送完成后，不要立刻调用 completeTransfer，
            // 而是继续保持在轮询状态，直到后端返回 status === 'completed' (代表接收方也拉取完了)
            progress.value = 100
            
            // 重新开启一个定时器检查最终完成状态
            const checkFinalStatus = async () => {
              const status = await getTransferStatus(taskId)
              if (status === 'completed') {
                if (statusTimer) {
                  clearInterval(statusTimer)
                  statusTimer = null
                }
                completeTransfer()
              }
            }
            statusTimer = window.setInterval(checkFinalStatus, 1000)

          } catch (e) {
            console.error('Push failed:', e)
            alert('推送失败: ' + e)
            cancelTransfer()
          }
        } else if (status === 'rejected' || status === 'cancelled') {
          if (statusTimer) {
            clearInterval(statusTimer)
            statusTimer = null
          }
          alert('传输被拒绝或取消')
          cancelTransfer()
        } else {
          waitCount++
          if (waitCount > 20) { // 60秒超时
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
