<template>
  <div v-if="previewFile" class="tab-pane preview-pane">
    <div class="preview-header">
      <h2>{{ previewFile.name }}</h2>
      <button @click="$emit('close')" class="close-btn">×</button>
    </div>
    <div class="preview-content">
      <div v-if="previewLoading" class="preview-loading">加载中...</div>
      <div v-else-if="previewError" class="preview-error">{{ previewError }}</div>
      <div v-else-if="previewFile.is_image" class="preview-image">
        <img :src="`/api/download/${previewFile.path}`" :alt="previewFile.name" />
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
import type { PreviewFile } from '../types'

defineProps<{
  previewFile: PreviewFile | null
  previewLoading: boolean
  previewError: string
}>()

defineEmits<{
  (e: 'close'): void
}>()
</script>

