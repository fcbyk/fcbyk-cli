<template>
  <main class="w-full max-w-[960px] p-7 bg-[#1e293b]/85 rounded-[18px] border border-white/6 shadow-(--shadow) backdrop-blur-md min-[881px]:h-auto max-[880px]:h-full max-[880px]:w-full max-[880px]:overflow-y-auto max-[880px]:rounded-none">
    <!-- 顶部工具栏 -->
    <div class="flex justify-between items-center mb-4">
      <p class="text-(--muted) text-sm m-0">
        列表数据来自本地配置文件，支持批量添加和管理。
      </p>
      <button 
        class="rounded-xl px-4 py-2.5 text-[14px] font-semibold cursor-pointer transition-all duration-150 text-white bg-linear-to-br from-(--primary) to-(--accent) shadow-[0_8px_20px_rgba(34,211,238,0.25)] active:translate-y-px active:shadow-none hover:shadow-[0_10px_25px_rgba(34,211,238,0.35)] flex items-center gap-2"
        @click="showAddModal = true"
      >
        <span class="text-lg">➕</span>
        <span>添加元素</span>
      </button>
    </div>

    <!-- 工具栏 -->
    <div class="flex flex-wrap gap-3 mb-[18px]">
      <button id="start-btn" 
        class="rounded-xl px-4 py-3 text-[15px] font-semibold cursor-pointer transition-all duration-150 text-[#0b1224] border-none bg-linear-to-br from-(--primary) to-(--accent) shadow-[0_12px_30px_rgba(34,211,238,0.18)] active:translate-y-px active:shadow-none disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none" 
        :disabled="isDrawing" @click="handleStartDraw">
        开始选择
      </button>
      <button class="rounded-xl px-4 py-3 text-[15px] font-semibold cursor-pointer transition-all duration-150 text-(--text) bg-white/12 border border-white/6 shadow-none active:translate-y-px active:shadow-none" @click="loadItems">刷新列表</button>

      <div class="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl bg-white/4 border border-white/6 cursor-pointer select-none transition-all hover:bg-white/6 hover:border-white/10" @click="toggleNoRepeatMode">
        <input type="checkbox" :checked="noRepeatMode" class="w-11 h-6 appearance-none bg-white/10 rounded-full relative cursor-pointer transition-colors duration-300 checked:bg-(--primary) before:content-[''] before:absolute before:w-5 before:h-5 before:rounded-full before:bg-white before:top-0.5 before:left-0.5 before:transition-transform before:duration-300 before:shadow-[0_2px_4px_rgba(0,0,0,0.2)] checked:before:translate-x-5" @click.stop @change="toggleNoRepeatMode">
        <label class="text-(--text) text-sm cursor-pointer">无放回模式</label>
      </div>

      <div class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-white/4 border border-white/6 text-sm">
        <label for="speed-slider" class="text-(--muted)">抽奖速度：</label>
        <input type="range" id="speed-slider" min="1" max="8" :value="drawSpeed" step="0.5" 
          class="flex-1 min-w-[120px] h-1.5 appearance-none bg-white/10 rounded-lg cursor-pointer accent-(--primary)" 
          @input="handleSpeedChange">
        <span class="text-(--primary) font-semibold min-w-[45px] text-right">{{ drawSpeed }}秒</span>
      </div>

      <button v-if="hasDrawn" class="rounded-xl px-4 py-3 text-[15px] font-semibold cursor-pointer transition-all duration-150 text-(--text) bg-white/12 border border-white/6 shadow-none active:translate-y-px active:shadow-none" @click="resetDrawn">
        重置已抽取
      </button>
    </div>

    <!-- 状态提示 -->
    <div :class="['px-3.5 py-3 rounded-xl bg-white/6 border border-white/5 text-sm flex items-center gap-2.5 mb-3.5', 
      statusType === 'ok' ? 'text-(--success)' : statusType === 'err' ? 'text-(--danger)' : 'text-(--muted)']">
      <span :class="['w-2.5 h-2.5 rounded-full shadow-[0_0_12px_rgba(34,211,238,0.7)]', 
        statusType === 'ok' ? 'bg-(--success)' : statusType === 'err' ? 'bg-(--danger)' : 'bg-(--primary)']"></span>
      {{ statusText }}
    </div>

    <!-- 主内容区 -->
    <div class="grid grid-cols-1 min-[881px]:grid-cols-[1fr_320px] gap-4">
      <!-- 候选列表 -->
      <section class="bg-white/4 border border-white/5 rounded-[14px] p-4">
        <div class="flex justify-between items-center mb-2.5">
          <h3 class="m-0 text-[17px] text-(--text)">候选列表</h3>
          <button 
            class="text-xs px-3 py-1.5 rounded-lg bg-white/10 border border-white/10 text-(--text) hover:bg-white/15 cursor-pointer transition-all"
            @click="loadItems"
          >
            🔄 刷新
          </button>
        </div>
        <div v-if="hasItems" class="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-2.5 pt-2.5 max-h-[50dvh] overflow-y-auto pr-1 scrollbar-hide">
          <div v-for="(item, idx) in items" :key="idx" 
            :class="['flex items-center gap-2.5 p-3 rounded-xl bg-white/5 border border-white/6 text-(--text) transition-all duration-150 wrap-break-word', 
              { 'border-primary/50! shadow-[0_8px_18px_rgba(34,211,238,0.18)] -translate-y-px': currentHighlightIndex === idx },
              { 'opacity-40 bg-white/2 border-white/3 pointer-events-none': drawnIndices.has(idx) }]">
            <span :class="['w-[30px] h-[30px] rounded-[10px] inline-flex items-center justify-center font-bold text-[13px]', 
              drawnIndices.has(idx) ? 'bg-gray-500/20 text-gray-500/60' : 'bg-(--primary)/20 text-(--primary)']">{{ idx + 1 }}</span>
            <span>{{ item }}</span>
          </div>
        </div>
        <p v-else class="text-(--muted) text-[13px]">
          列表为空，请点击右上角「添加元素」或批量导入。
        </p>
      </section>

      <!-- 结果面板 -->
      <section class="bg-white/4 border border-white/5 rounded-[14px] p-4">
        <h3 class="m-0 mb-2.5 text-[17px] text-(--text)">最终结果</h3>
        <div class="bg-linear-to-br from-(--primary)/12 to-(--accent)/12 border border-(--primary)/35 rounded-[14px] p-[18px] min-h-[140px] flex flex-col justify-center gap-2.5 text-center">
          <div v-if="selectedWinner" class="text-(--muted) tracking-[0.4px]">本轮选中</div>
          <div v-else class="text-(--muted) tracking-[0.4px]">点击「开始」随机选出一项</div>

          <div class="text-[32px] font-extrabold text-(--primary) [text-shadow:0_6px_24px_rgba(34,211,238,0.3)] wrap-break-word">{{ selectedWinner || '—' }}</div>

          <div v-if="selectedWinner" class="text-(--muted) text-[13px]">
            数据来源：本地配置文件 ~/.fcbyk/pick.json
          </div>
          <div v-if="noRepeatMode && hasDrawn" class="text-(--muted) text-[13px]">
            已抽取 {{ drawnIndices.size }}/{{ items.length }} 项
          </div>
        </div>
      </section>
    </div>

    <!-- 添加元素弹窗 -->
    <div v-if="showAddModal" class="fixed inset-0 z-1000 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" @click="showAddModal = false">
      <div class="w-full max-w-[500px] bg-[#1e293b] rounded-[18px] border border-white/10 shadow-2xl overflow-hidden" @click.stop>
        <!-- 标题 -->
        <div class="flex justify-between items-center p-5 border-b border-white/10">
          <h3 class="text-xl font-bold text-(--text) m-0">添加抽奖元素</h3>
          <button class="w-8 h-8 rounded-lg bg-white/5 border border-white/10 text-(--muted) hover:text-(--text) hover:bg-white/10 cursor-pointer flex items-center justify-center transition-all" @click="showAddModal = false">
            ✕
          </button>
        </div>

        <!-- 内容 -->
        <div class="p-5">
          <label class="block text-sm text-(--muted) mb-2">
            输入元素（支持多个元素，使用以下方式分隔）：
          </label>
          <ul class="text-xs text-(--muted) mb-3 space-y-1">
            <li>• 回车换行</li>
            <li>• 逗号 ,</li>
            <li>• 分号 ;</li>
          </ul>
          <textarea 
            v-model="addItemsInput"
            placeholder="例如：&#10;张三&#10;李四&#10;王五"
            rows="8"
            class="w-full p-4 rounded-xl border border-slate-400/60 bg-slate-900/80 text-(--text) text-[15px] outline-none focus:border-(--primary) focus:shadow-[0_0_0_1px_rgba(34,211,238,0.4)] resize-none scrollbar-hide"
            @keydown.meta.enter="handleBatchAdd"
          ></textarea>
          
          <!-- 提示信息 -->
          <div v-if="addMessage" :class="['mt-3 p-3 rounded-xl text-sm', 
            addMessageType === 'success' ? 'bg-(--success)/10 text-(--success) border border-(--success)/30' : 
            addMessageType === 'error' ? 'bg-(--danger)/10 text-(--danger) border border-(--danger)/30' : 
            'bg-white/5 text-(--muted) border border-white/10']">
            {{ addMessage }}
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="flex justify-end gap-3 p-5 border-t border-white/10 bg-white/2">
          <button 
            class="rounded-xl px-5 py-2.5 text-[15px] font-semibold cursor-pointer transition-all duration-150 text-(--text) bg-white/10 border border-white/10 hover:bg-white/15"
            @click="showAddModal = false"
          >
            取消
          </button>
          <button 
            class="rounded-xl px-5 py-2.5 text-[15px] font-semibold cursor-pointer transition-all duration-150 text-white bg-linear-to-br from-(--primary) to-(--accent) shadow-[0_8px_20px_rgba(34,211,238,0.25)] active:translate-y-px disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="!addItemsInput.trim() || isAdding"
            @click="handleBatchAdd"
          >
            {{ isAdding ? '添加中...' : '确认添加' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePick } from './composables/usePick'
import { useAnimation } from './composables/useAnimation'
import { addItems as apiAddItems } from './api'

const {
  items,
  drawnIndices,
  noRepeatMode,
  drawSpeed,
  isDrawing,
  statusText,
  statusType,
  selectedWinner,
  hasItems,
  hasDrawn,
  availableIndices,
  setStatus,
  loadItems,
  resetDrawn,
  toggleNoRepeatMode,
  updateSpeed,
  markAsDrawn,
  setWinner
} = usePick()

const {
  currentHighlightIndex,
  stopAnimation,
  spinToTarget
} = useAnimation()

// 添加元素相关状态
const showAddModal = ref(false)
const addItemsInput = ref('')
const addMessage = ref('')
const addMessageType = ref<'success' | 'error' | ''>('')
const isAdding = ref(false)

// 处理速度变化
function handleSpeedChange(e: Event) {
  const target = e.target as HTMLInputElement
  updateSpeed(parseFloat(target.value))
}

// 批量添加元素
async function handleBatchAdd() {
  if (!addItemsInput.value.trim()) {
    return
  }

  isAdding.value = true
  addMessage.value = ''
  addMessageType.value = ''

  try {
    const result = await apiAddItems(addItemsInput.value)
    
    if (result.addedCount > 0) {
      addMessage.value = `成功添加 ${result.addedCount} 个元素`
      addMessageType.value = 'success'
      
      // 清空输入框
      addItemsInput.value = ''
      
      // 刷新列表
      await loadItems()
      
      // 成功后自动关闭弹窗（延迟一点让用户看到提示）
      setTimeout(() => {
        showAddModal.value = false
      }, 1000)
    }
    
    if (result.duplicates.length > 0) {
      addMessage.value = `添加了 ${result.addedCount} 个元素，${result.duplicates.length} 个重复项已跳过`
      addMessageType.value = result.addedCount > 0 ? 'success' : ''
    }
  } catch (error) {
    addMessage.value = (error as Error).message || '添加失败'
    addMessageType.value = 'error'
  } finally {
    isAdding.value = false
  }
}

// 开始抽奖
async function handleStartDraw() {
  if (!hasItems.value) {
    setStatus('列表为空，请先添加候选项', 'err')
    return
  }

  if (availableIndices.value.length === 0) {
    setStatus('所有项目已抽取完毕，请点击「重置已抽取」或刷新列表', 'err')
    return
  }

  isDrawing.value = true
  setStatus('正在选择...')
  stopAnimation()

  try {
    // 从可用索引中随机选择
    const randomPos = Math.floor(Math.random() * availableIndices.value.length)
    const targetIndex = availableIndices.value[randomPos]
    const winner = items.value[targetIndex]

    // 计算速度因子
    const speedFactor = drawSpeed.value / 3

    // 执行动画
    await spinToTarget(targetIndex, availableIndices.value, speedFactor)

    // 标记为已抽取
    markAsDrawn(targetIndex)

    // 设置结果
    setWinner(winner)
    setStatus('选择完成！', 'ok')
  } catch (error) {
    stopAnimation()
    setStatus((error as Error).message || '随机选择失败', 'err')
  } finally {
    isDrawing.value = false
  }
}

// 初始化
onMounted(() => {
  loadItems()
})
</script>
