<template>
  <div class="flex flex-col h-full p-[20px] m-5">
    <!-- 需要密码但尚未验证：隐藏上传框，展示登录卡片 -->
    <div v-if="requirePassword && !canUpload" class="flex-1 min-h-0 flex items-center justify-center p-6">
      <div class="w-[min(380px,92%)] px-5 py-[22px]">
        <div class="text-base font-semibold text-[#111827] text-center">需要验证密码</div>
        <div class="mt-2 text-[13px] leading-relaxed text-[#6b7280] text-center">上传已开启密码保护</div>

        <input
          v-if="showPasswordInput"
          ref="passwordInputRef"
          class="mt-[14px] w-full px-3 py-2.5 text-sm leading-5 rounded-[10px] border border-[#e5e7eb] outline-none bg-white text-[#111827] focus:border-[#111827]"
          :class="{ shake: shouldShake }"
          :value="password"
          type="password"
          placeholder="请输入密码"
          autocomplete="off"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
          @input="onPasswordInput"
          @keydown.enter="onLoginClick"
          @animationend="onShakeEnd"
        />

        <div class="mt-[18px] flex justify-center">
          <button class="appearance-none border border-[#111827] bg-transparent text-[#111827] text-sm font-semibold px-[18px] py-2.5 rounded-[10px] cursor-pointer transition-colors duration-150 ease-in-out hover:text-[#2ecc71] hover:border-[#2ecc71]" type="button" @click="onLoginClick">
            {{ showPasswordInput ? '确认密码' : '输入密码' }}
          </button>
        </div>

        <div class="mt-3 text-[12px] text-[#ef4444] text-center min-h-[18px] opacity-0 transition-opacity duration-160 ease-in-out" :class="{ 'opacity-100': !!passwordError }">
          {{ passwordError }}
        </div>
      </div>
    </div>

    <div
      v-else
      class="border-2 border-dashed border-[#3498db] rounded-lg p-5 text-center cursor-pointer transition-all duration-300 grow flex items-center justify-center md:min-h-[150px] min-w-0 hover:bg-[#f8f9fa] w-full"
      :class="{ 'bg-[#e8f4f8] border-[#2980b9]': isDragOver, 'opacity-70 cursor-wait': isUploading }"
      :style="{
        pointerEvents: canUpload ? 'auto' : 'none',
        opacity: canUpload ? '1' : '0.5'
      }"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
      @click="onUploadAreaClick"
    >
      <div>
        <div class="text-[48px] text-[#3498db] mb-2.5">📤</div>
        <p class="text-[#7f8c8d] text-base mt-2">{{ isDragOver ? '松开上传' : uploadHint }}</p>
        <p v-if="uploadPathHint" class="text-[#95a5a6] text-[13px] mt-1.5 opacity-70 font-normal">{{ uploadPathHint }}</p>
      </div>
      <input ref="fileInputRef" type="file" multiple style="display: none" @change="onFileSelect" />
    </div>

    <!-- 上传进度 -->
    <div v-if="showProgress" class="mt-4 w-full shrink-0">
      <div class="h-5 bg-[#f0f0f0] rounded-[10px] overflow-hidden w-full">
        <div class="h-full bg-[#2ecc71] w-0 transition-[width] duration-300" :style="{ width: `${overallProgress}%` }"></div>
      </div>

      <div class="mt-2.5 text-sm text-[#666] wrap-break-word md:text-[12px] md:leading-[1.35]">
        <div v-for="(line, idx) in statusLines" :key="idx" class="upload-line">
          <span>{{ line }}</span>
        </div>
      </div>

      <div v-if="uploadStatsText" class="mt-1.5 text-[12px] opacity-85 wrap-break-word md:text-[11px] md:leading-[1.35]">
        <div v-for="(line, idx) in statsLines" :key="idx" class="upload-line">
          <span>{{ line }}</span>
        </div>
      </div>

      <div v-if="queueLength > 0" class="mt-2.5 text-[12px] text-[#7f8c8d]">队列中还有 {{ queueLength }} 个文件等待上传</div>
    </div>
    <div v-if="showCompleteInfoFlag" class="mt-4 w-full px-3.5 py-2.5 bg-[#e8f5e9] text-[#2e7d32] rounded-md text-[13px] font-medium leading-relaxed shadow-sm border-l-[3px] border-[#4caf50] animate-in fade-in slide-in-from-bottom-1 duration-300">{{ completeInfo }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'

const shouldShake = ref(false)
let shakeTimer: number | undefined

const props = defineProps<{
  canUpload: boolean
  isDragOver: boolean
  isUploading: boolean
  uploadHint: string
  uploadPathHint?: string
  requirePassword: boolean
  password: string
  passwordError: string
  showProgress: boolean
  queueLength: number
  overallProgress: number
  uploadStatus: string
  uploadStatsText: string
  completeInfo: string
  showCompleteInfoFlag: boolean
}>()

const emit = defineEmits<{
  (e: 'verify-password'): void
  (e: 'update:password', v: string): void
  (e: 'files-selected', files: File[]): void
  (e: 'dragover', ev: DragEvent): void
  (e: 'dragleave', ev: DragEvent): void
  (e: 'drop', ev: DragEvent): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const passwordInputRef = ref<HTMLInputElement | null>(null)
const showPasswordInput = ref(false)

// 移动端：把长信息拆成多行，减少频繁换行导致的“闪动”
const isMobile = computed(() => window.matchMedia && window.matchMedia('(max-width: 768px)').matches)

const statusLines = computed<string[]>(() => {
  const text = (props.uploadStatus || '').trim()
  if (!text) return []

  if (!isMobile.value) return [text]

  // e.g. "正在上传: Windows.iso (4.42 GB / 4.42 GB) - 100%"
  // 拆成两行：
  // 正在上传: Windows.iso
  // (4.42 GB / 4.42 GB) - 100%
  const idx = text.indexOf(' (')
  if (idx > 0) {
    const line1 = text.slice(0, idx).trim()
    const line2 = text.slice(idx).trim()
    return [line1, line2].filter(Boolean)
  }

  return [text]
})

const statsLines = computed<string[]>(() => {
  const text = (props.uploadStatsText || '').trim()
  if (!text) return []

  if (!isMobile.value) return [text]

  // 把 " · " 拆成两行展示，避免一行过长在移动端抖动
  const parts = text.split(' · ').map((s) => s.trim()).filter(Boolean)
  if (parts.length <= 2) return [text]

  const half = Math.ceil(parts.length / 2)
  const line1 = parts.slice(0, half).join(' · ')
  const line2 = parts.slice(half).join(' · ')
  return [line1, line2].filter(Boolean)
})

watch(
  () => props.canUpload,
  (v) => {
    // 登录成功后：复位登录界面
    if (v) {
      showPasswordInput.value = false
    }
  }
)

watch(
  () => props.passwordError,
  (msg) => {
    // 密码错误时，给输入框一个抖动反馈，避免整块内容因重渲染产生“闪”的观感
    if (!msg) return
    if (!showPasswordInput.value) return

    shouldShake.value = false
    if (shakeTimer) window.clearTimeout(shakeTimer)
    // 强制下一帧重新加 class，确保重复错误也能再次触发动画
    shakeTimer = window.setTimeout(() => {
      shouldShake.value = true
    }, 0)
  }
)

function onPasswordInput(e: Event) {
  emit('update:password', (e.target as HTMLInputElement).value)
}

function onLoginClick() {
  // 第一次点击：仅展开输入框
  if (!showPasswordInput.value) {
    showPasswordInput.value = true
    nextTick(() => {
      passwordInputRef.value?.focus()
    })
    return
  }

  // 第二次点击：执行验证
  emit('verify-password')
}

function onShakeEnd() {
  shouldShake.value = false
}

function onDragOver(ev: DragEvent) {
  if (!props.canUpload) return
  if (ev.dataTransfer) {
    ev.dataTransfer.dropEffect = 'copy'
  }
  emit('dragover', ev)
}

function onDragLeave(ev: DragEvent) {
  if (!props.canUpload) return
  emit('dragleave', ev)
}

function onDrop(ev: DragEvent) {
  if (!props.canUpload) return
  emit('drop', ev)
}

function onUploadAreaClick() {
  if (!props.canUpload) return
  fileInputRef.value?.click()
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) {
    emit('files-selected', Array.from(target.files))
  }
  // 清空 input，确保可以重复选择同一文件
  target.value = ''
}
</script>

<style scoped>
/* 仅做轻量抖动反馈，避免整块 login-card 重新渲染导致的“闪”感 */
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
</style>