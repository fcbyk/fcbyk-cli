<template>
  <div v-if="previewFile" class="tab-pane preview-pane">
    <div class="preview-header">
      <h2>{{ previewFile.name }}</h2>
      <button @click="$emit('close')" class="close-btn">×</button>
    </div>
    <div class="preview-content">
      <div v-if="previewLoading" class="preview-loading">加载中...</div>
      <div v-else-if="previewError" class="preview-error">{{ previewError }}</div>
      <div v-else-if="isVideo" class="preview-video">
        <video :src="videoSrc" controls preload="metadata" playsinline />
        <div class="preview-actions">
          <a :href="`/api/download/${previewFile.path}`" class="download-btn" download>下载文件</a>
        </div>
      </div>
      <div v-else-if="previewFile.is_image" class="preview-image">
        <img :src="`/api/download/${encodeURI(previewFile.path)}`" :alt="previewFile.name" />
      </div>
      <div v-else-if="previewFile.is_binary" class="preview-binary">
        <p>无法预览二进制文件</p>
        <a :href="`/api/download/${previewFile.path}`" class="download-btn" download>下载文件</a>
      </div>
      <pre v-else class="preview-text"><code>{{ previewFile.content }}</code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PreviewFile } from '../types'

const props = defineProps<{
  previewFile: PreviewFile | null
  previewLoading: boolean
  previewError: string
}>()

const isVideo = computed(() => {
  const name = (props.previewFile?.name || '').toLowerCase()
  return name.endsWith('.mp4') || name.endsWith('.webm') || name.endsWith('.ogg')
})

const videoSrc = computed(() => {
  if (!props.previewFile) return ''
  // 走后端新增的 Range 预览接口，支持拖动进度条/快进
  return `/api/preview/${encodeURI(props.previewFile.path)}`
})

defineEmits<{
  (e: 'close'): void
}>()
</script>

