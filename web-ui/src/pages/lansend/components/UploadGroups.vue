<template>
  <div v-if="groupedUploads.length > 0" class="flex flex-col gap-1.5">
    <div
      v-for="group in groupedUploads"
      :key="group.path"
      class="relative border rounded-md overflow-hidden shadow-sm transition-all duration-300"
      :class="group.remainingSize === 0 ? 'bg-[#f0f9eb] border-[#e1f3d8]' : 'bg-white border-[#e1f3d8]'"
    >
      <div
        v-if="group.remainingSize > 0"
        class="absolute inset-0 bg-[#f0f9eb] transition-[width] duration-500 ease-linear pointer-events-none"
        :style="{ width: `${group.totalProgress}%` }"
      ></div>

      <div class="relative px-2 py-2 flex items-center justify-between cursor-pointer hover:bg-[#e8f5e9]/50 transition-colors">
        <div class="flex items-center gap-2 min-w-0 flex-1" @click="toggleUploadExpand(group.path)">
          <div
            class="p-1 rounded-md text-white shadow-sm flex-none"
            :class="group.remainingSize === 0 ? 'bg-[#67c23a]' : 'bg-[#2ecc71]'"
          >
            <Check v-if="group.remainingSize === 0" class="w-3.5 h-3.5 stroke-3" />
            <Layers v-else class="w-3.5 h-3.5" />
          </div>
          <div class="flex items-center gap-2 min-w-0 flex-1 mr-2">
            <span class="text-sm font-bold text-[#2c3e50] truncate" :title="group.statusText">
              {{ group.statusText }}
            </span>
          </div>
        </div>
        <div class="flex items-center gap-2 flex-none ml-2">
          <div class="flex flex-col items-end leading-none gap-0.5">
            <span v-if="group.remainingSize > 0" class="text-[12px] font-bold text-[#2ecc71]">
              {{ Math.round(group.totalProgress) }}%
            </span>
            <div
              v-if="group.remainingSize > 0"
              class="flex items-center gap-1.5 text-[10px] text-[#909399] font-normal"
            >
              <span v-if="group.remainingTimeText" class="whitespace-nowrap">
                {{ group.remainingTimeText }}
              </span>
              <span class="whitespace-nowrap">
                / 剩 {{ formatFileSize(group.remainingSize) }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-1 flex-none ml-1 relative z-10">
            <button
              v-if="group.remainingSize === 0"
              type="button"
              @click="onClearGroup(group.path, $event)"
              @touchend="onClearGroup(group.path, $event)"
              class="p-2 text-[#909399] hover:text-[#ef4444] active:text-[#ef4444] active:bg-[#fee2e2] rounded-md transition-all touch-manipulation flex items-center justify-center"
              title="移除已完成记录"
            >
              <X class="w-4.5 h-4.5 pointer-events-none" />
            </button>
            <button
              type="button"
              class="p-1 flex items-center justify-center rounded-md touch-manipulation"
              @click.stop="toggleUploadExpand(group.path)"
              aria-label="切换展开状态"
            >
              <ChevronDown
                v-if="!isUploadExpanded[group.path]"
                class="w-4 h-4 text-[#909399] pointer-events-none"
              />
              <ChevronUp
                v-else
                class="w-4 h-4 text-[#909399] pointer-events-none"
              />
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="isUploadExpanded[group.path]"
        class="relative z-1 bg-[#fafafa] border-t border-[#e1f3d8] max-h-[200px] md:max-h-[150px] overflow-y-auto"
      >
        <div
          v-for="task in group.tasks"
          :key="task.id"
          class="px-2 py-2.5 md:py-1.5 border-b border-[#f0f9eb] last:border-0 flex items-center justify-between gap-2 hover:bg-[#f0f9eb]/50 transition-colors"
        >
          <div class="flex items-center gap-2 min-w-0 flex-1">
            <span class="text-sm md:text-[12px] flex-none">📄</span>
            <span
              class="text-[13px] md:text-[11px] text-[#606266] truncate flex-1"
              :title="task.file.name"
            >
              {{ task.file.name }}
            </span>
          </div>
          <div class="flex items-center gap-2 flex-none">
            <span
              class="text-[11px] md:text-[10px] font-mono font-medium"
              :class="{
                'text-[#ef4444]': task.status === 'error',
                'text-[#2ecc71]': task.status === 'uploading' || task.status === 'completed',
                'text-[#909399]': task.status === 'pending'
              }"
            >
              <template v-if="task.status === 'uploading'">
                {{ Math.round(task.progress) }}%
              </template>
              <template v-else-if="task.status === 'pending'">
                等待
              </template>
              <template v-else-if="task.status === 'error'">
                失败
              </template>
              <template v-else-if="task.status === 'completed'">
                已完成
              </template>
            </span>
            <button
              v-if="task.status !== 'completed'"
              @click.stop="emitCancelUpload(task.id)"
              class="p-2 md:p-0.5 text-[#909399] hover:text-[#ef4444] active:text-[#ef4444] active:bg-[#fee2e2] rounded-md transition-all touch-manipulation"
            >
              <X class="w-4 h-4 md:w-3 md:h-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { UploadTask } from '../composables/useLansendUpload'
import { X, ChevronDown, ChevronUp, Layers, Check } from 'lucide-vue-next'
import { formatFileSize } from '@/utils/files'
import { useUploadTaskGroups } from '../composables/useUploadTaskGroups'

const props = defineProps<{
  uploadTasks?: UploadTask[]
  uploadSpeed?: number
}>()

const emit = defineEmits<{
  (e: 'cancel-upload', taskId: string): void
  (e: 'clear-group-tasks', path: string): void
}>()

const isUploadExpanded = ref<Record<string, boolean>>({})

const { groupedUploads } = useUploadTaskGroups(
  () => props.uploadTasks,
  () => props.uploadSpeed
)

watch(
  () => groupedUploads.value,
  newGroups => {
    newGroups.forEach(group => {
      if (isUploadExpanded.value[group.path] === undefined) {
        isUploadExpanded.value[group.path] = false
      }
    })
  },
  { deep: true, immediate: true }
)

function toggleUploadExpand(path: string) {
  isUploadExpanded.value[path] = !isUploadExpanded.value[path]
}

function emitCancelUpload(taskId: string) {
  emit('cancel-upload', taskId)
}

function onClearGroup(path: string, ev: Event) {
  ev.stopPropagation()
  ev.preventDefault()
  emit('clear-group-tasks', path)
}
</script>

