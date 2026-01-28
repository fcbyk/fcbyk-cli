<template>
  <div 
    class="w-64 bg-background-dark/90 border border-primary/30 rounded-2xl p-4 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in duration-300"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-white font-bold text-sm">发送文件</h3>
      <button @click="$emit('cancel')" class="text-white/40 hover:text-white transition-colors">
        <XIcon class="size-4" />
      </button>
    </div>

    <!-- 拖拽/选择区域 -->
    <div 
      v-if="!file"
      class="border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-2 transition-all cursor-pointer group"
      :class="[isDragging ? 'border-primary bg-primary/10' : 'border-white/10 hover:border-primary/40 hover:bg-primary/5']"
      @click="triggerFileSelect"
    >
      <input type="file" ref="fileInput" class="hidden" @change="onFileChange" />
      <div class="size-10 rounded-full bg-primary/10 flex items-center justify-center group-hover:scale-110 transition-transform">
        <UploadIcon class="size-5 text-primary" />
      </div>
      <p class="text-[11px] text-white/60 text-center">拖拽文件到此处或 <span class="text-primary">点击上传</span></p>
    </div>

    <!-- 已选择文件展示 -->
    <div v-else class="bg-white/5 rounded-xl p-3 border border-white/5 flex items-center gap-3 mb-4">
      <div class="size-10 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
        <FileIcon class="size-5 text-primary" />
      </div>
      <div class="min-w-0 flex-1">
        <p class="text-xs text-white font-medium truncate">{{ file.name }}</p>
        <p class="text-[10px] text-white/40">{{ formatSize(file.size) }}</p>
      </div>
      <button @click="$emit('remove')" class="text-white/20 hover:text-red-400 transition-colors shrink-0">
        <TrashIcon class="size-3.5" />
      </button>
    </div>

    <!-- 发送按钮 -->
    <button 
      v-if="file"
      @click="$emit('send')"
      class="w-full bg-primary text-background-dark py-2.5 rounded-xl text-xs font-bold hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(19,200,236,0.3)]"
    >
      <SendIcon class="size-3.5" />
      确认发送
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  X as XIcon, 
  Upload as UploadIcon, 
  File as FileIcon, 
  Trash2 as TrashIcon,
  Send as SendIcon
} from 'lucide-vue-next'
import type { TransferFile } from '../types'

defineProps<{
  file: TransferFile | null
}>()

const emit = defineEmits<{
  (e: 'select', file: File): void
  (e: 'remove'): void
  (e: 'send'): void
  (e: 'cancel'): void
}>()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const triggerFileSelect = () => {
  fileInput.value?.click()
}

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    emit('select', target.files[0])
  }
}

const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer?.files.length) {
    emit('select', e.dataTransfer.files[0])
  }
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>
