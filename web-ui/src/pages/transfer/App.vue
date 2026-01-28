<template>
  <main class="relative min-h-screen w-full flex items-center justify-center overflow-hidden">
    <!-- 背景网格（在 style.css 中定义） -->
    
    <!-- 传输链路 (SVG 层) -->
    <svg 
      class="absolute inset-0 w-full h-full pointer-events-none z-10"
    >
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <g v-if="activeTransfer" :transform="`translate(${windowSize.width / 2}, ${windowSize.height / 2})`">
        <!-- 背景发光层 (更宽更模糊) -->
        <g class="opacity-30">
          <line :x1="sender?.x" :y1="sender?.y" x2="0" y2="0" stroke="var(--color-primary)" stroke-width="6" stroke-linecap="round" filter="url(#glow)" class="link-glow" />
          <line v-if="!isServerTarget" x1="0" y1="0" :x2="activeTarget?.x" :y2="activeTarget?.y" stroke="var(--color-primary)" stroke-width="6" stroke-linecap="round" filter="url(#glow)" class="link-glow" />
        </g>
        
        <!-- 主链路 -->
        <line 
          :x1="sender?.x" :y1="sender?.y" 
          x2="0" y2="0" 
          stroke="var(--color-primary)" 
          stroke-width="2" 
          class="transfer-link link-main"
        />
        <line 
          v-if="!isServerTarget"
          x1="0" y1="0" 
          :x2="activeTarget?.x" :y2="activeTarget?.y" 
          stroke="var(--color-primary)" 
          stroke-width="2" 
          class="transfer-link link-main"
        />
      </g>
    </svg>

    <!-- 用户节点 -->
    <div
      v-for="user in users"
      :key="user.id"
      class="absolute transition-all duration-700 ease-out"
      :class="[
        (activeTargetId === user.id || (user.isMe && isReceivePreparing)) ? 'z-40' : 'z-20'
      ]"
      :style="{
        left: `calc(50% + ${user.x}px)`,
        top: `calc(50% + ${user.y}px)`,
        transform: 'translate(-50%, -50%)'
      }"
    >
      <div class="relative flex flex-col items-center">
        <!-- 圆形图标容器 -->
        <div 
          class="size-16 rounded-full bg-background-dark border-2 flex items-center justify-center hover:scale-110 transition-all cursor-pointer group relative shrink-0"
          :class="[
            (user.isMe || activeTargetId === user.id) ? 'border-primary shadow-[0_0_15px_rgba(19,200,236,0.4)]' : 'border-white/20 hover:border-primary/60',
            activeTargetId === user.id ? 'scale-110' : ''
          ]"
          style="will-change: transform;"
          @click="handleUserClick(user)"
        >
          <component 
            :is="user.icon" 
            class="size-8 transition-colors"
            :class="[
              user.isMe || activeTargetId === user.id ? 'text-primary' : 'text-white/60 group-hover:text-primary'
            ]"
          />
          
          <!-- 我 的标识 -->
          <div v-if="user.isMe" class="absolute -bottom-1 -right-1 bg-primary text-background-dark text-[10px] font-bold px-1.5 rounded-full border-2 border-background-dark">
            ME
          </div>

          <!-- 消息提醒 (仅对我显示) -->
          <div v-if="user.isMe && receiveRequest && !isReceiving" class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full size-6 flex items-center justify-center animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.5)] border-2 border-background-dark">
            <MessageIcon class="size-3 fill-current" />
          </div>

          <!-- 传输状态标识 -->
          <!-- 发送中：我在发 -->
          <div v-if="activeTransfer && user.isMe && !isReceiving" class="absolute -top-1 -right-1 bg-primary text-background-dark rounded-full size-5 flex items-center justify-center animate-bounce">
            <UploadIcon class="size-3 stroke-[3px]" />
          </div>
          <!-- 接收中：我在收 -->
          <div v-if="isReceiving && user.isMe" class="absolute -top-1 -right-1 bg-primary text-background-dark rounded-full size-5 flex items-center justify-center animate-bounce">
            <DownloadIcon class="size-3 stroke-[3px]" />
          </div>
          <!-- 接收中：对方在发 -->
          <div v-if="isReceiving && receiveRequest?.sender.id === user.id" class="absolute -top-1 -right-1 bg-primary text-background-dark rounded-full size-5 flex items-center justify-center animate-bounce">
            <UploadIcon class="size-3 stroke-[3px]" />
          </div>
          <!-- 发送中：对方在收 -->
          <div v-if="activeTransfer && !isReceiving && activeTarget?.id === user.id" class="absolute -top-1 -right-1 bg-primary text-background-dark rounded-full size-5 flex items-center justify-center animate-bounce">
            <DownloadIcon class="size-3 stroke-[3px]" />
          </div>

          <!-- 完成勾选 -->
          <div v-if="transferStatus === 'completed' && activeTarget?.id === user.id" class="absolute inset-0 bg-primary/20 rounded-full flex items-center justify-center backdrop-blur-sm animate-in fade-in">
            <CheckIcon class="text-primary size-8 stroke-[4px]" />
          </div>
        </div>

        <!-- 设备名称 (绝对定位，不占用中心点) -->
        <div class="absolute top-full mt-2 bg-background-dark/60 px-3 py-1 rounded-full border border-white/10 backdrop-blur-sm whitespace-nowrap">
          <p class="text-[11px] font-medium text-white/80">{{ user.name }}</p>
        </div>

        <!-- 发送卡片 (当该节点被点击且处于准备状态时显示) -->
        <div 
          v-if="isPreparing && activeTargetId === user.id" 
          class="absolute top-full mt-10 z-50"
        >
          <FileUploadCard 
            :file="selectedFile"
            @select="handleFileSelect"
            @remove="selectedFile = null"
            @send="startTransfer"
            @cancel="cancelTransfer"
          />
        </div>

        <!-- 接收卡片 (当我被点击且有待处理请求时显示) -->
        <div 
          v-if="user.isMe && isReceivePreparing && receiveRequest" 
          class="absolute top-full mt-10 z-50"
        >
          <FileReceiveCard 
            :request="receiveRequest"
            @accept="acceptReceive"
            @reject="rejectReceive"
          />
        </div>
      </div>
    </div>

    <!-- 中心服务器 -->
    <div 
      class="absolute transition-all duration-700"
      :class="[
        activeTargetId === -1 ? 'z-40' : 'z-30'
      ]"
      style="left: 50%; top: 50%; transform: translate(-50%, -50%);"
    >
      <div class="relative flex flex-col items-center">
        <!-- 服务器圆圈 -->
        <div 
          class="size-20 rounded-full bg-background-dark border-4 flex items-center justify-center pulse-glow relative shrink-0 transition-all cursor-pointer hover:scale-105"
          :class="[
            activeTargetId === -1 ? 'border-primary shadow-[0_0_20px_rgba(19,200,236,0.6)]' : 'border-primary'
          ]"
          @click="handleServerClick"
        >
          <MonitorIcon class="text-primary size-10" />
          <div class="absolute -bottom-1 -right-1 size-5 bg-green-500 rounded-full border-4 border-background-dark"></div>

          <!-- 传输状态标识 -->
          <div v-if="activeTransfer" class="absolute -top-1 -right-1 bg-primary text-background-dark rounded-full size-6 flex items-center justify-center animate-bounce">
            <DownloadIcon v-if="isServerTarget || isReceiving" class="size-4 stroke-[3px]" />
            <UploadIcon v-else class="size-4 stroke-[3px]" />
          </div>

          <!-- 完成勾选 -->
          <div v-if="transferStatus === 'completed' && isServerTarget" class="absolute inset-0 bg-primary/20 rounded-full flex items-center justify-center backdrop-blur-sm animate-in fade-in">
            <CheckIcon class="text-primary size-10 stroke-[4px]" />
          </div>
        </div>
        
        <!-- 服务器文字 (绝对定位) -->
        <div class="absolute top-full mt-3 text-center whitespace-nowrap">
          <p class="text-white font-bold text-sm text-shadow-glow">中心服务器</p>
          <p class="text-primary/70 font-mono text-[10px]">192.168.1.1</p>
        </div>

        <!-- 上传卡片 (当服务器被点击且处于准备状态时显示) -->
        <div 
          v-if="isPreparing && activeTargetId === -1" 
          class="absolute top-full mt-12 z-50"
        >
          <FileUploadCard 
            :file="selectedFile"
            @select="handleFileSelect"
            @remove="selectedFile = null"
            @send="startTransfer"
            @cancel="cancelTransfer"
          />
        </div>
      </div>
    </div>

    <!-- 进度条提示 -->
    <div v-if="activeTransfer" class="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 bg-background-dark/80 border border-primary/40 backdrop-blur-md px-6 py-4 rounded-2xl flex flex-col gap-2 min-w-[300px] shadow-2xl">
      <div class="flex items-center justify-between text-xs mb-1">
        <span class="text-white font-medium flex items-center gap-2">
          <FileIcon class="size-3 text-primary" />
          {{ isReceiving ? receiveRequest?.file.name : selectedFile?.name }}
        </span>
        <span class="text-primary font-bold">{{ progress }}%</span>
      </div>
      <div class="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
        <div 
          class="h-full bg-primary transition-all duration-300 ease-out shadow-[0_0_10px_rgba(19,200,236,0.6)]"
          :style="{ width: `${progress}%` }"
        ></div>
      </div>
      <p class="text-[10px] text-white/40 text-center mt-1">
        {{ isReceiving ? `正在从 ${receiveRequest?.sender.name} 接收文件...` : `正在加密传输到 ${activeTarget?.name}...` }}
      </p>
    </div>

    <!-- 完成提示 -->
    <div v-if="transferStatus === 'completed'" class="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 bg-green-500/20 border border-green-500/40 backdrop-blur-md px-8 py-3 rounded-full flex items-center gap-3 animate-in fade-in slide-in-from-bottom-4">
      <div class="size-2 bg-green-500 rounded-full"></div>
      <p class="text-white text-sm font-bold">{{ isReceiving ? '文件接收成功！' : '传输完成！' }}</p>
    </div>
  </main>
</template>

<script setup lang="ts">
import { 
  Monitor as MonitorIcon, 
  Upload as UploadIcon,
  Download as DownloadIcon,
  File as FileIcon,
  Check as CheckIcon,
  MessageCircle as MessageIcon
} from 'lucide-vue-next'
import { useTransfer } from './composables/useTransfer'
import FileUploadCard from './components/FileUploadCard.vue'
import FileReceiveCard from './components/FileReceiveCard.vue'

const {
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
  rejectReceive
} = useTransfer()
</script>

<style scoped>
.text-shadow-glow {
  text-shadow: 0 0 10px rgba(19, 200, 236, 0.5);
}

.animate-in {
  animation-duration: 0.3s;
  animation-timing-function: ease-out;
  animation-fill-mode: both;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes zoom-in {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

@keyframes slide-in-from-bottom-4 {
  from { transform: translateY(1rem); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.fade-in { animation-name: fade-in; }
.zoom-in { animation-name: zoom-in; }
.slide-in-from-bottom-4 { animation-name: slide-in-from-bottom-4; }
</style>
