<template>
  <div
    ref="sidebarRef"
    class="sidebar"
    :class="{ 'mobile-open': isSidebarOpen }"
    :style="{ width: sidebarWidth + 'px' }"
  >
    <div class="file-tree">
      <div v-if="!fileTree || fileTree.length === 0" class="loading">
        加载目录结构
      </div>
      <div v-else>
        <FileTreeItem
          v-for="(item, index) in fileTree"
          :key="index"
          :item="item"
          :level="0"
          :active-file="activeFile"
          @file-selected="$emit('file-selected', $event)"
        />
      </div>
    </div>
  </div>
  <div
    ref="resizerRef"
    class="resizer"
    :class="{ dragging: isResizing }"
    @mousedown="handleResizeStart"
  ></div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import FileTreeItem from './FileTreeItem.vue'

interface FileTreeItem {
  name: string
  path: string
  is_dir: boolean
  children?: FileTreeItem[]
}

const props = defineProps<{
  fileTree: FileTreeItem[]
  sidebarWidth: number
  isSidebarOpen: boolean
  activeFile: string | null
}>()

const emit = defineEmits<{
  'file-selected': [path: string]
  'toggle-sidebar': []
  'sidebar-resize': [width: number]
}>()

const sidebarRef = ref<HTMLElement | null>(null)
const isResizing = ref(false)

let startX = 0
let startWidth = 0

function handleResizeStart(e: MouseEvent) {
  if (!sidebarRef.value) return
  isResizing.value = true
  startX = e.clientX
  startWidth = sidebarRef.value.offsetWidth

  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  e.preventDefault()

  const mouseMoveHandler = (e: MouseEvent) => {
    if (!isResizing.value || !sidebarRef.value) return
    const diff = e.clientX - startX
    const newWidth = startWidth + diff
    const minWidth = 150
    const maxWidth = window.innerWidth * 0.5
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      emit('sidebar-resize', newWidth)
    }
  }

  const mouseUpHandler = () => {
    if (isResizing.value) {
      isResizing.value = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.removeEventListener('mousemove', mouseMoveHandler)
    document.removeEventListener('mouseup', mouseUpHandler)
  }

  document.addEventListener('mousemove', mouseMoveHandler)
  document.addEventListener('mouseup', mouseUpHandler)
}

// 监听文件选择，在移动端自动关闭侧边栏
watch(
  () => props.activeFile,
  () => {
    if (props.activeFile && window.innerWidth <= 768) {
      setTimeout(() => {
        emit('toggle-sidebar')
      }, 100)
    }
  }
)
</script>
