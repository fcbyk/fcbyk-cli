<template>
  <div class="tab-pane upload-pane">
    <div
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
      </div>
      <input
        ref="fileInputRef"
        type="file"
        multiple
        style="display: none"
        @change="onFileSelect"
      />
    </div>

    <!-- 密码输入 -->
    <div v-if="requirePassword" class="password-input">
      <input
        :value="password"
        type="password"
        placeholder="请输入上传密码"
        @input="onPasswordInput"
        @keydown.enter="onVerifyPassword"
      />
      <button @click="onVerifyPassword">验证</button>
      <div v-if="passwordError" class="password-error">{{ passwordError }}</div>
    </div>

    <!-- 上传进度 -->
    <div v-if="showProgress" class="upload-progress">
      <div class="progress-bar">
        <div class="progress" :style="{ width: `${overallProgress}%` }"></div>
      </div>
      <div class="upload-status">{{ uploadStatus }}</div>
      <div v-if="queueLength > 0" class="queue-info">
        队列中还有 {{ queueLength }} 个文件等待上传
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  canUpload: boolean
  isDragOver: boolean
  isUploading: boolean
  uploadHint: string
  requirePassword: boolean
  password: string
  passwordError: string
  showProgress: boolean
  queueLength: number
  overallProgress: number
  uploadStatus: string
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

function onVerifyPassword() {
  emit('verify-password')
}

function onPasswordInput(e: Event) {
  const v = (e.target as HTMLInputElement).value
  emit('update:password', v)
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

