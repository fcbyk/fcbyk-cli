<template>
  <main class="w-full max-w-[960px] p-7 bg-[#1e293b]/85 rounded-[18px] border border-white/6 shadow-(--shadow) backdrop-blur-md min-[881px]:h-auto max-[880px]:h-full max-[880px]:w-full max-[880px]:overflow-y-auto max-[880px]:rounded-none">
    <p class="mb-4 text-(--muted) text-sm">
      列表数据直接来自命令行的配置文件，使用 <code>fcbyk pick --add</code> 即可更新。
    </p>

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
        <h3 class="m-0 mb-2.5 text-[17px] text-(--text)">候选列表</h3>
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
          列表为空，请在终端执行 <code>fcbyk pick --add 项目</code> 添加。
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
  </main>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { usePick } from './composables/usePick'
import { useAnimation } from './composables/useAnimation'

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

// 处理速度变化
function handleSpeedChange(e: Event) {
  const target = e.target as HTMLInputElement
  updateSpeed(parseFloat(target.value))
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
