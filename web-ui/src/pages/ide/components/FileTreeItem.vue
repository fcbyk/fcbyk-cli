<template>
  <div
    class="tree-item"
    :class="{
      expanded: isExpanded,
      active: activeFile === item.path
    }"
    :data-type="item.is_dir ? 'dir' : 'file'"
    :data-path="item.path"
    :data-ext="!item.is_dir ? getFileExt(item.name) : undefined"
    @click.stop="handleClick"
  >
    <div class="tree-item-row">
      <div class="tree-item-indent" :style="{ width: level * 16 + 'px', minWidth: level * 16 + 'px' }"></div>
      <div class="tree-item-expander"></div>
      <div class="tree-item-wrapper">
        <span class="tree-item-icon"></span>
        <span class="tree-item-name">{{ item.name }}</span>
      </div>
    </div>
    <div v-if="item.is_dir && item.children && item.children.length > 0" class="tree-item-children">
      <FileTreeItem
        v-for="(child, index) in item.children"
        :key="index"
        :item="child"
        :level="level + 1"
        :active-file="activeFile"
        @file-selected="$emit('file-selected', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface FileTreeItem {
  name: string
  path: string
  is_dir: boolean
  children?: FileTreeItem[]
}

const props = defineProps<{
  item: FileTreeItem
  level: number
  activeFile: string | null
}>()

const emit = defineEmits<{
  'file-selected': [path: string]
}>()

const isExpanded = ref(false)

function getFileExt(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || ''
}

function handleClick() {
  if (props.item.is_dir) {
    isExpanded.value = !isExpanded.value
  } else {
    emit('file-selected', props.item.path)
  }
}
</script>
