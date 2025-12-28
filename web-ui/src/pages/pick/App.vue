<template>
    <main class="card">
      <p class="desc">
        列表数据直接来自命令行的配置文件，使用 <code>fcbyk pick --add</code> 即可更新。
      </p>
  
      <!-- 工具栏 -->
      <div class="toolbar">
        <button 
          id="start-btn" 
          class="primary" 
          :disabled="isDrawing"
          @click="handleStartDraw"
        >
          开始选择
        </button>
        <button class="secondary" @click="loadItems">刷新列表</button>
        
        <div class="toggle-switch" @click="toggleNoRepeatMode">
          <input 
            type="checkbox" 
            :checked="noRepeatMode"
            @click.stop
            @change="toggleNoRepeatMode"
          >
          <label>无放回模式</label>
        </div>
  
        <div class="speed-control">
          <label for="speed-slider">抽奖速度：</label>
          <input 
            type="range" 
            id="speed-slider" 
            min="1" 
            max="8" 
            :value="drawSpeed"
            step="0.5"
            @input="handleSpeedChange"
          >
          <span class="speed-value">{{ drawSpeed }}秒</span>
        </div>
  
        <button 
          v-if="hasDrawn" 
          class="secondary" 
          @click="resetDrawn"
        >
          重置已抽取
        </button>
      </div>
  
      <!-- 状态提示 -->
      <div class="status" :class="statusType">
        <span class="badge-dot"></span>
        {{ statusText }}
      </div>
  
      <!-- 主内容区 -->
      <div class="layout">
        <!-- 候选列表 -->
        <section class="panel">
          <h3>候选列表</h3>
          <div v-if="hasItems" class="list">
            <div
              v-for="(item, idx) in items"
              :key="idx"
              class="item"
              :class="{
                active: currentHighlightIndex === idx,
                drawn: drawnIndices.has(idx)
              }"
            >
              <span class="badge">{{ idx + 1 }}</span>
              <span>{{ item }}</span>
            </div>
          </div>
          <p v-else class="muted">
            列表为空，请在终端执行 <code>fcbyk pick --add 项目</code> 添加。
          </p>
        </section>
  
        <!-- 结果面板 -->
        <section class="panel">
          <h3>最终结果</h3>
          <div class="result">
            <div v-if="selectedWinner" class="title">本轮选中</div>
            <div v-else class="title">点击「开始」随机选出一项</div>
            
            <div class="value">{{ selectedWinner || '—' }}</div>
            
            <div v-if="selectedWinner" class="muted">
              数据来源：本地配置文件 ~/.fcbyk/pick.json
            </div>
            <div v-if="noRepeatMode && hasDrawn" class="muted">
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