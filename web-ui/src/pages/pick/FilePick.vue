<template>
  <main class="card">
    <h1>文件抽奖</h1>
    <p class="desc">
      通过随机生成的 4 位抽奖码进行抽奖，每个抽奖码只能成功抽取一次。抽中的文件可无限次下载，用于课后给学生随机分配作品 / 素材。
    </p>

    <div class="toolbar">
      <div class="redeem">
        <input v-model="codeInput" type="text" placeholder="输入 4 位抽奖码" maxlength="10" :disabled="isDrawing"
          @keyup.enter="handleStartDraw" />
        <button class="primary" :disabled="isDrawing || !hasFiles" @click="handleStartDraw">
          使用抽奖码抽文件
        </button>
      </div>
      <div class="speed-control">
        <label for="speed-slider">抽奖速度：</label>
        <input id="speed-slider" type="range" min="1" max="8" :value="drawSpeed" step="0.5"
          @input="handleSpeedChange" />
        <span class="speed-value">{{ drawSpeed }}秒</span>
      </div>
      <button class="secondary" @click="loadFiles">刷新列表</button>
    </div>

    <div class="status">
      <div class="left">
        <span class="badge-dot"></span>
        <span>{{ statusText }}</span>
      </div>
      <div class="counter">{{ counterText }}</div>
    </div>

    <div class="layout">
      <section class="panel">
        <h3>候选文件</h3>
        <div v-if="hasFiles" class="list">
          <div v-for="(file, idx) in files" :key="idx" class="item" :class="{ active: currentHighlightIndex === idx }">
            <div class="name">{{ file.name }}</div>
            <div class="meta">大小：{{ formatSize(file.size) }}</div>
          </div>
        </div>
        <p v-else class="muted" id="empty-hint">
          目录下没有可用文件，请检查命令行指定的路径。
        </p>
      </section>

      <section class="panel">
        <h3>抽取结果</h3>
        <div class="result">
          <div class="title">
            {{ selectedFile ? '本轮抽中' : '输入抽奖码并点击「使用抽奖码抽文件」随机选出一个文件' }}
          </div>
          <div class="value">{{ selectedFile ? selectedFile.name : '—' }}</div>
          <a v-if="selectedFile && downloadUrl" :href="downloadUrl" download>
            点击下载
          </a>
          <div v-if="selectedFile" class="muted">
            大小：{{ formatSize(selectedFile.size) }}
          </div>
          <div class="muted">{{ limitHint }}</div>
        </div>
        <div class="history">
          <div class="history-title">已抽中的文件（本页）：</div>
          <ul class="history-list">
            <li v-if="!hasHistory">暂无记录</li>
            <li v-else v-for="(item, idx) in history" :key="idx">
              <a class="name" :href="`/api/files/download/${encodeURIComponent(item.name)}`" download>
                {{ item.name }}
              </a>
              <span class="size">{{ formatSize(item.size || 0) }}</span>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useFilePick } from './composables/useFilePick'
import { useAnimation } from './composables/useAnimation'

const {
  files,
  history,
  drawSpeed,
  isDrawing,
  statusText,
  selectedFile,
  downloadUrl,
  codeInput,
  hasFiles,
  hasHistory,
  counterText,
  limitHint,
  formatSize,
  loadFiles,
  startDraw,
  completeDraw,
  failDraw,
  updateSpeed,
  setStatus,
  init
} = useFilePick()

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
  if (!hasFiles.value) {
    return
  }

  try {
    stopAnimation()
    const result = await startDraw()
    if (!result) return

    // 执行动画
    setStatus('正在抽奖中...')
    if (result.targetIndex >= 0) {
      // 使用所有文件索引进行动画
      const allIndices = files.value.map((_, idx) => idx)
      const speedFactor = drawSpeed.value / 3
      await spinToTarget(result.targetIndex, allIndices, speedFactor)
    }

    // 动画完成后显示结果
    completeDraw(result.file, result.downloadUrl)
    result.updateHistory()
  } catch (error) {
    setStatus((error as Error).message || '抽取失败', 'err')
    failDraw()
  }
}

// 初始化
onMounted(() => {
  // 初始化数据
  init()

  // 监听页面显示事件
  window.addEventListener('pageshow', handlePageShow)
})

onUnmounted(() => {
  window.removeEventListener('pageshow', handlePageShow)
})

function handlePageShow() {
  loadFiles()
}
</script>

<style scoped>
.card {
  width: 100%;
  max-width: 980px;
  background: rgba(30, 41, 59, 0.9);
  padding: 24px;
}

h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

p.desc {
  margin: 0 0 14px;
}

.toolbar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 10px 0 16px;
}

button {
  padding: 11px 16px;
  font-size: 15px;
  font-weight: 700;
}

.status {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.status .left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 14px;
}

.badge-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.8);
}

.counter {
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text);
  font-weight: 700;
  font-size: 14px;
}

.layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

.panel {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  padding: 16px;
}

.panel h3 {
  margin: 0 0 12px;
  font-size: 17px;
}

.list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.item {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 8px;
  word-break: break-all;
  transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.item .name {
  font-weight: 700;
  color: var(--text);
}

.item .meta {
  color: var(--muted);
  font-size: 12px;
}

.item.active {
  border-color: rgba(34, 211, 238, 0.5);
  box-shadow: 0 8px 18px rgba(34, 211, 238, 0.18);
  transform: translateY(-1px);
}

.result {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.12), rgba(168, 85, 247, 0.12));
  border: 1px solid rgba(34, 211, 238, 0.35);
  border-radius: 14px;
  padding: 18px;
  min-height: 140px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}

.result .title {
  color: var(--muted);
  letter-spacing: 0.4px;
}

.result .value {
  font-size: 22px;
  font-weight: 800;
  color: var(--primary);
  word-break: break-all;
}

.result a {
  color: var(--text);
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-decoration: none;
  font-weight: 700;
  display: inline-flex;
  gap: 6px;
  align-items: center;
  width: fit-content;
}

.muted {
  color: var(--muted);
  font-size: 13px;
}

.redeem {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.redeem input {
  flex: 1 1 180px;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.6);
  background: rgba(15, 23, 42, 0.8);
  color: var(--text);
  font-size: 14px;
  outline: none;
}

.redeem input::placeholder {
  color: rgba(148, 163, 184, 0.9);
}

.redeem input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.4);
}

.redeem input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.history {
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid rgba(148, 163, 184, 0.4);
}

.history-title {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 6px;
}

.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 160px;
  overflow-y: auto;
  font-size: 13px;
  color: var(--muted);
}

.history-list li {
  padding: 4px 0;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.history-list .name {
  font-weight: 600;
  color: var(--text);
  word-break: break-all;
  text-decoration: none;
}

.history-list .name:hover {
  text-decoration: underline;
}

.history-list .size {
  white-space: nowrap;
}
</style>
