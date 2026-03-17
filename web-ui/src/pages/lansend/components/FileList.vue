<template>
  <div
    class="file-list-container flex flex-col flex-1 min-h-0 m-4 md:m-0 relative"
    @dragover.prevent="onDragOver"
    @dragenter.prevent="onDragEnter"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <div
      v-if="isDragOver"
      class="absolute inset-0 z-50 bg-[#e8f4f8] border-2 border-dashed border-[#3498db] rounded-lg flex items-center justify-center text-center p-5 transition-all duration-300 pointer-events-none"
    >
      <div>
        <div class="text-[48px] text-[#3498db] mb-2.5">📤</div>
        <p class="text-[#3498db] text-lg font-medium mt-2">松开上传</p>
        <p v-if="uploadPathHint" class="text-[#95a5a6] text-[13px] mt-1.5 opacity-80 font-normal">{{ uploadPathHint }}</p>
      </div>
    </div>

    <div v-show="!isDragOver" class="flex flex-col flex-1 min-h-0">
      <div class="flex-none sticky top-0 z-20 bg-white pb-2">
        <div class="mb-2 p-2 bg-[#f8f9fa] rounded-md flex flex-wrap items-center gap-[2px] text-sm leading-relaxed border border-[#eee] relative">
          <div class="flex items-center gap-[2px] flex-1 min-w-0 flex-wrap">
            <div class="flex items-center gap-[2px]">
              <span @click="emitNavigate('')" class="text-[#606266] px-[6px] py-[2px] rounded transition-all duration-200 cursor-pointer whitespace-nowrap hover:bg-[#e4e7ed] hover:text-[#409eff] active:bg-[#e4e7ed]">{{ shareName }}</span>
              <span v-if="pathParts.length > 0" class="text-[#909399] text-[12px] select-none mx-[2px]">/</span>
            </div>
            <template v-for="(part, index) in pathParts" :key="index">
              <div class="flex items-center gap-[2px] last:text-[#303133] last:font-medium last:cursor-default">
                <span @click="emitNavigate(part.path)" class="text-[#606266] px-[6px] py-[2px] rounded transition-all duration-200 cursor-pointer whitespace-nowrap hover:bg-[#e4e7ed] hover:text-[#409eff] active:bg-[#e4e7ed] last:cursor-default last:hover:bg-transparent last:hover:text-[#303133]">{{ part.name }}</span>
                <span v-if="index < pathParts.length - 1" class="text-[#909399] text-[12px] select-none mx-[2px]">/</span>
              </div>
            </template>
          </div>
          <div v-if="shouldShowUploadButton" class="flex-none flex items-center ml-1">
            <button 
              @click="onUploadButtonClick"
              class="p-2 md:p-1.5 rounded-md hover:bg-[#e4e7ed] active:bg-[#e4e7ed] text-[#606266] transition-colors duration-200 flex items-center gap-1 touch-manipulation" :title="needsPassword ? '需要密码上传' : '上传文件'"
            >
              <Lock v-if="needsPassword" class="w-5 h-5 md:w-4 md:h-4 text-[#f39c12]" />
              <Upload v-else class="w-5 h-5 md:w-4 md:h-4" />
            </button>
            <input ref="fileInputRef" type="file" multiple style="display: none" @change="onFileSelect" />
          </div>
        </div>

        <div v-if="showPasswordInput && needsPassword" class="mb-2 p-3 bg-white border border-[#d1d5db] rounded-lg animate-in fade-in slide-in-from-top-1 duration-300">
          <div class="flex items-center justify-between mb-3 md:mb-2">
            <div class="text-[13px] md:text-[12px] font-medium text-[#374151]">请输入上传密码</div>
            <button @click="showPasswordInput = false" class="text-[#9ca3af] hover:text-[#6b7280] active:bg-[#f3f4f6] transition-colors p-2 md:p-1 rounded-md touch-manipulation">
              <X class="w-4 h-4 md:w-3.5 md:h-3.5" />
            </button>
          </div>
          
          <div class="flex gap-2">
            <input
              ref="passwordInputRef"
              class="flex-1 px-3 py-2 md:py-1.5 text-sm rounded-md border border-[#e5e7eb] outline-none bg-white text-[#111827] focus:border-[#409eff] transition-colors"
              :class="{ shake: shouldShake }"
              :value="password"
              type="password"
              placeholder="上传密码"
              @input="onPasswordInput"
              @keydown.enter="onLoginClick"
              @animationend="onShakeEnd"
            />
            <button 
              class="px-4 py-2 md:px-3 md:py-1.5 bg-[#409eff] text-white text-sm font-medium rounded-md hover:bg-[#66b1ff] active:bg-[#3a8ee6] transition-colors disabled:opacity-50 touch-manipulation"
              @click="onLoginClick"
            >
              验证
            </button>
          </div>
          <div v-if="passwordError" class="mt-1 text-[11px] text-[#ef4444] font-medium">{{ passwordError }}</div>
        </div>

        <div v-if="showCompleteInfoFlag" class="mb-2 w-full px-3 py-2.5 md:py-2 bg-[#fffbeb] text-[#854d0e] rounded-md text-[13px] md:text-[12px] font-medium leading-relaxed border border-[#f59e0b]/50 flex items-center gap-2 animate-in fade-in slide-in-from-bottom-1 duration-300">
          <div class="flex-none w-4 h-4 bg-[#f59e0b] rounded-full flex items-center justify-center">
            <AlertCircle class="w-3 h-3 text-white stroke-3" />
          </div>
          <span class="flex-1">{{ completeInfo }}</span>
          <button @click="emit('close-complete-info')" class="flex-none p-2 md:p-1 hover:bg-[#fef3c7] active:bg-[#fef3c7] rounded-md transition-colors touch-manipulation">
            <X class="w-4 h-4 md:w-3.5 md:h-3.5" />
          </button>
        </div>

        <UploadGroups
          v-if="uploadTasks && uploadTasks.length > 0"
          :upload-tasks="uploadTasks"
          :upload-speed="uploadSpeed"
          @cancel-upload="emitCancelUpload"
          @clear-all-tasks="emitClearAll"
          @show-details="emitShowDetails"
        />
      </div>

      <ul class="file-list list-none p-0 w-full grow overflow-y-auto overflow-x-hidden min-h-0">
      <li v-if="loading" style="padding: 20px; text-align: center; color: #999;">加载中...</li>
      <li v-else-if="error" style="padding: 20px; text-align: center; color: #e74c3c;">{{ error }}</li>
      <li v-else-if="(!items || items.length === 0)" style="padding: 20px; text-align: center; color: #999;">
        目录为空
      </li>
      <template v-else>
        <li v-for="item in items" :key="item.path" 
            class="group p-2.5 border-b border-[#eee] flex flex-col w-full hover:bg-[#f8f9fa] transition-all duration-300 relative overflow-hidden cursor-pointer"
            @click="emitItemClick(item)">
          <div class="flex items-center justify-between w-full relative z-1">
            <div class="flex items-center grow min-w-0 overflow-hidden">
              <span class="mr-2.5 w-6 text-center flex-none">
                <span v-if="item.is_dir" class="text-[#f39c12]">📁</span>
                <span v-else class="text-[#3498db]">📄</span>
              </span>
              <span class="flex items-center grow min-w-0 overflow-hidden text-ellipsis whitespace-nowrap">
                <span class="text-[#3498db] no-underline overflow-hidden text-ellipsis whitespace-nowrap hover:underline">{{ item.name }}</span>
              </span>
            </div>

            <!-- 正常文件的下载按钮 -->
            <a
              v-if="!unDownload && !item.is_dir"
              :href="`/api/download/${item.path}`"
              class="bg-[#2ecc71] text-white border-none px-[10px] py-[5px] rounded cursor-pointer no-underline text-[12px] flex-none ml-2.5 hover:bg-[#27ae60]"
              download
              @click.stop
              >下载</a
            >
          </div>
        </li>
      </template>
    </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import type { DirectoryItem, PathPart } from '../types'
import type { UploadTask } from '../composables/useLansendUpload'
import { X, Upload, Lock, AlertCircle } from 'lucide-vue-next'
import UploadGroups from './UploadGroups.vue'
import { usePasswordShake } from '../composables/usePasswordShake'

const props = defineProps<{
  shareName: string
  pathParts: PathPart[]
  items: DirectoryItem[]
  loading: boolean
  error: string
  unDownload?: boolean
  // 上传相关 props
  uploadTasks?: UploadTask[]
  uploadSpeed?: number
  canUpload?: boolean
  isDragOver?: boolean
  isUploading?: boolean
  showProgress?: boolean
  queueLength?: number
  overallProgress?: number
  uploadStatus?: string
  uploadStatsText?: string
  uploadPathHint?: string
  completeInfo?: string
  showCompleteInfoFlag?: boolean
  // 密码验证相关 props
  requirePassword?: boolean
  password?: string
  passwordError?: string
  unUpload?: boolean
}>()

const passwordInputRef = ref<HTMLInputElement | null>(null)
const showPasswordInput = ref(false)

const { shouldShake, onShakeEnd } = usePasswordShake(
  () => props.passwordError,
  () => showPasswordInput.value
)

// 是否需要验证密码才能上传
const needsPassword = computed(() => props.requirePassword && !props.canUpload)

// 是否显示上传按钮
const shouldShowUploadButton = computed(() => !props.unUpload)

const emit = defineEmits<{
  (e: 'navigate', path: string): void
  (e: 'item-click', item: any): void
  (e: 'dragover', ev: DragEvent): void
  (e: 'dragenter', ev: DragEvent): void
  (e: 'dragleave', ev: DragEvent): void
  (e: 'drop', ev: DragEvent): void
  (e: 'files-selected', files: File[]): void
  (e: 'cancel-upload', taskId: string): void
  (e: 'clear-all-tasks'): void
  (e: 'show-details'): void
  (e: 'close-complete-info'): void
  (e: 'verify-password'): void
  (e: 'update:password', v: string): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)

function onUploadButtonClick() {
  if (needsPassword.value) {
    showPasswordInput.value = true
    nextTick(() => {
      passwordInputRef.value?.focus()
    })
    return
  }
  fileInputRef.value?.click()
}

function onPasswordInput(e: Event) {
  emit('update:password', (e.target as HTMLInputElement).value)
}

function onLoginClick() {
  emit('verify-password')
}

watch(
  () => props.canUpload,
  (v: boolean | undefined) => {
    // 登录成功后：复位登录界面
    if (v) {
      showPasswordInput.value = false
    }
  }
)

function onFileSelect(ev: Event) {
  const target = ev.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    emit('files-selected', Array.from(target.files))
  }
  target.value = ''
}

function emitCancelUpload(taskId: string) {
  emit('cancel-upload', taskId)
}

function emitClearAll() {
  emit('clear-all-tasks')
}

function emitShowDetails() {
  emit('show-details')
}

function onDragOver(ev: DragEvent) {
  if (!props.canUpload) return
  ev.stopPropagation()
  if (ev.dataTransfer) {
    ev.dataTransfer.dropEffect = 'copy'
  }
  emit('dragover', ev)
}

function onDragEnter(ev: DragEvent) {
  if (!props.canUpload) return
  emit('dragenter', ev)
}

function onDragLeave(ev: DragEvent) {
  if (!props.canUpload) return
  emit('dragleave', ev)
}

function onDrop(ev: DragEvent) {
  if (!props.canUpload) return
  ev.stopPropagation()
  emit('drop', ev)
}

function emitNavigate(path: string) {
  emit('navigate', path)
}

function emitItemClick(item: DirectoryItem) {
  emit('item-click', item)
}
</script>

<style scoped>
.file-list::-webkit-scrollbar {
  width: 8px;
}

.file-list::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 10px;
}

.file-list-container:hover .file-list::-webkit-scrollbar-thumb {
  background: #ccc;
}

.file-list::-webkit-scrollbar-thumb:hover {
  background: #bbb;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: fadeIn 0.3s ease-out;
}

.shake {
  animation: shake-x 320ms ease-in-out;
}

@keyframes shake-x {
  0%, 100% { transform: translateX(0); }
  15% { transform: translateX(-6px); }
  30% { transform: translateX(6px); }
  45% { transform: translateX(-5px); }
  60% { transform: translateX(5px); }
  75% { transform: translateX(-3px); }
  90% { transform: translateX(3px); }
}
</style>

