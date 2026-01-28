<template>
  <div 
    class="w-64 bg-background-dark/90 border border-primary/30 rounded-2xl p-4 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in duration-300"
  >
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-white font-bold text-sm">接收文件</h3>
      <button @click="$emit('close')" class="text-white/40 hover:text-white transition-colors">
        <XIcon class="size-4" />
      </button>
    </div>

    <!-- 发送者信息 -->
    <div class="flex items-center gap-2 mb-4 p-2 bg-white/5 rounded-lg border border-white/5">
      <div class="size-8 rounded-full bg-primary/10 flex items-center justify-center">
        <component :is="request.sender.icon" class="size-4 text-primary" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="text-[10px] text-white/40 leading-none mb-1">来自</p>
        <p class="text-xs text-white font-medium truncate">{{ request.sender.name }}</p>
      </div>
    </div>

    <!-- 文件详情 -->
    <div class="bg-white/5 rounded-xl p-3 border border-white/5 flex items-center gap-3 mb-4">
      <div class="size-10 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
        <FileIcon class="size-5 text-primary" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="text-xs text-white font-medium truncate">{{ request.file.name }}</p>
        <p class="text-[10px] text-white/40">{{ formatSize(request.file.size) }}</p>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="grid grid-cols-2 gap-2">
      <button 
        @click="$emit('reject')"
        class="bg-white/5 text-white/60 py-2 rounded-xl text-xs font-bold hover:bg-white/10 transition-all border border-white/5"
      >
        拒绝
      </button>
      <button 
        @click="$emit('accept')"
        class="bg-primary text-background-dark py-2 rounded-xl text-xs font-bold hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(19,200,236,0.3)]"
      >
        同意接收
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  X as XIcon, 
  File as FileIcon
} from 'lucide-vue-next'
import type { ReceiveRequest } from '../types'

defineProps<{
  request: ReceiveRequest
}>()

defineEmits<{
  (e: 'accept'): void
  (e: 'reject'): void
  (e: 'close'): void
}>()

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>
