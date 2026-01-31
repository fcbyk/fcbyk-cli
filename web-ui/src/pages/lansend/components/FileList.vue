<template>
  <div class="file-list-container flex flex-col flex-1 min-h-0 m-4 md:m-0">
    <div class="mb-[15px] p-2 bg-[#f8f9fa] rounded-md flex flex-wrap items-center gap-[2px] text-sm leading-relaxed border border-[#eee]">
      <div class="flex items-center gap-[2px]">
        <span @click="emitNavigate('')" class="text-[#606266] px-[6px] py-[2px] rounded transition-all duration-200 cursor-pointer whitespace-nowrap hover:bg-[#e4e7ed] hover:text-[#409eff]">{{ shareName }}</span>
        <span class="text-[#909399] text-[12px] select-none mx-[2px]">/</span>
      </div>
      <template v-for="(part, index) in pathParts" :key="index">
        <div class="flex items-center gap-[2px] last:text-[#303133] last:font-medium last:cursor-default">
          <span @click="emitNavigate(part.path)" class="text-[#606266] px-[6px] py-[2px] rounded transition-all duration-200 cursor-pointer whitespace-nowrap hover:bg-[#e4e7ed] hover:text-[#409eff] last:cursor-default last:hover:bg-transparent last:hover:text-[#303133]">{{ part.name }}</span>
          <span class="text-[#909399] text-[12px] select-none mx-[2px] last:hidden">/</span>
        </div>
      </template>
    </div>

    <ul class="file-list list-none p-0 w-full grow overflow-y-auto overflow-x-hidden min-h-0">
      <li v-if="loading" style="padding: 20px; text-align: center; color: #999;">加载中...</li>
      <li v-else-if="error" style="padding: 20px; text-align: center; color: #e74c3c;">{{ error }}</li>
      <li v-else-if="!items || items.length === 0" style="padding: 20px; text-align: center; color: #999;">
        目录为空
      </li>
      <li v-else v-for="item in items" :key="item.path" class="p-2.5 border-b border-[#eee] flex items-center justify-between w-full hover:bg-[#f8f9fa]">
        <div class="flex items-center grow min-w-0 overflow-hidden" @click="emitItemClick(item)">
          <span class="mr-2.5 w-6 text-center flex-none">
            <span v-if="item.is_dir" class="text-[#f39c12]">📁</span>
            <span v-else class="text-[#3498db]">📄</span>
          </span>
          <span class="flex items-center grow min-w-0 overflow-hidden text-ellipsis whitespace-nowrap">
            <span class="text-[#3498db] no-underline overflow-hidden text-ellipsis whitespace-nowrap hover:underline cursor-pointer">{{ item.name }}</span>
          </span>
        </div>
        <a
          v-if="!unDownload && !item.is_dir"
          :href="`/api/download/${item.path}`"
          class="bg-[#2ecc71] text-white border-none px-[10px] py-[5px] rounded cursor-pointer no-underline text-[12px] flex-none ml-2.5 hover:bg-[#27ae60]"
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

<style scoped>
.file-list::-webkit-scrollbar {
  width: 8px;
}

/* 默认隐藏滚动条滑块 */
.file-list::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 10px;
}

/* 当鼠标移入整个组件根容器时，显示列表的滚动条滑块 */
.file-list-container:hover .file-list::-webkit-scrollbar-thumb {
  background: #ccc;
}

/* 鼠标移入滑块本身时颜色加深 */
.file-list::-webkit-scrollbar-thumb:hover {
  background: #bbb;
}
</style>

