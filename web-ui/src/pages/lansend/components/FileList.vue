<template>
  <div class="file-list-wrapper">
    <div class="current-path">
      <span class="path-separator">/</span>
      <span @click="emitNavigate('')" class="path-link">{{ shareName }}</span>
      <span class="path-separator">/</span>
      <template v-for="(part, index) in pathParts" :key="index">
        <span @click="emitNavigate(part.path)" class="path-link">{{ part.name }}</span>
        <span class="path-separator">/</span>
      </template>
    </div>

    <ul class="file-list">
      <li v-if="loading" style="padding: 20px; text-align: center; color: #999;">加载中...</li>
      <li v-else-if="error" style="padding: 20px; text-align: center; color: #e74c3c;">{{ error }}</li>
      <li v-else-if="!items || items.length === 0" style="padding: 20px; text-align: center; color: #999;">
        目录为空
      </li>
      <li v-else v-for="item in items" :key="item.path" class="file-item">
        <div class="file-info" @click="emitItemClick(item)">
          <span class="file-icon">
            <span v-if="item.is_dir" class="folder-icon">📁</span>
            <span v-else class="file-icon">📄</span>
          </span>
          <span class="file-name">
            <span class="file-link">{{ item.name }}</span>
          </span>
        </div>
        <a
          v-if="!unDownload && !item.is_dir"
          :href="`/api/download/${item.path}`"
          class="download-btn"
          download
          @click.stop
          >下载</a
        >
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import type { DirectoryItem, PathPart } from '../types'

defineProps<{
  shareName: string
  pathParts: PathPart[]
  items: DirectoryItem[]
  loading: boolean
  error: string
  unDownload?: boolean
}>()

const emit = defineEmits<{
  (e: 'navigate', path: string): void
  (e: 'itemClick', item: DirectoryItem): void
}>()

function emitNavigate(path: string) {
  emit('navigate', path)
}

function emitItemClick(item: DirectoryItem) {
  emit('itemClick', item)
}
</script>

