<template>
  <div class="tab-pane upload-pane">
    <!-- 需要密码但尚未验证：隐藏上传框，展示登录卡片 -->
    <div v-if="requirePassword && !canUpload" class="login-gate">
      <div class="login-card">
        <div class="login-title">需要登录后才能上传</div>
        <div class="login-subtitle">本分享已开启上传密码保护</div>

        <input
          v-if="showPasswordInput"
          ref="passwordInputRef"
          class="login-password-input"
          :class="{ shake: shouldShake }"
          :value="password"
          type="password"
          placeholder="请输入上传密码"
          autocomplete="off"
          autocapitalize="off"
          autocorrect="off"
          spellcheck="false"
          @input="onPasswordInput"
          @keydown.enter="onLoginClick"
          @animationend="onShakeEnd"
        />

        <div class="login-actions">
          <button class="login-btn" type="button" @click="onLoginClick">
            {{ showPasswordInput ? '登录' : '输入密码' }}
          </button>
        </div>

        <div class="login-error" :class="{ visible: !!passwordError }">
          {{ passwordError }}
        </div>
      </div>
    </div>

    <div
      v-else
      class="upload-area"
      :class="{ dragover: isDragOver, uploading: isUploading }"
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
        <div class="upload-icon">📤</div>
        <p class="upload-hint">{{ uploadHint }}</p>
        <p v-if="uploadPathHint" class="upload-path-hint">{{ uploadPathHint }}</p>
      </div>
      <input ref="fileInputRef" type="file" multiple style="display: none" @change="onFileSelect" />
    </div>

    <!-- 上传进度 -->
    <div v-if="showProgress" class="upload-progress">
      <div class="progress-bar">
        <div class="progress" :style="{ width: `${overallProgress}%` }"></div>
      </div>
      <div class="upload-status">{{ uploadStatus }}</div>
      <div v-if="queueLength > 0" class="queue-info">队列中还有 {{ queueLength }} 个文件等待上传</div>
    </div>
    <div v-if="showCompleteInfoFlag" class="complete-info">{{ completeInfo }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

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
}
</script>

<style scoped>
/* 仅做轻量抖动反馈，避免整块 login-card 重新渲染导致的“闪”感 */
.login-password-input.shake {
  animation: shake-x 320ms ease-in-out;
}

/* 错误文案区域始终占位，避免 v-if 造成布局抖动/闪烁 */
.login-error {
  min-height: 18px;
  opacity: 0;
  transition: opacity 160ms ease;
}

.login-error.visible {
  opacity: 1;
}

@keyframes shake-x {
  0% {
    transform: translateX(0);
  }
  15% {
    transform: translateX(-6px);
  }
  30% {
    transform: translateX(6px);
  }
  45% {
    transform: translateX(-5px);
  }
  60% {
    transform: translateX(5px);
  }
  75% {
    transform: translateX(-3px);
  }
  90% {
    transform: translateX(3px);
  }
  100% {
    transform: translateX(0);
  }
}
</style>
