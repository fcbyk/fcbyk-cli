<template>
  <div v-if="previewFile" class="tab-pane preview-pane">
    <div class="preview-content">
      <div v-if="previewLoading" class="preview-loading">加载中...</div>
      <div v-else-if="previewError" class="preview-error">
        <div class="preview-error-msg">{{ previewError }}</div>
        <a
          v-if="shouldShowOpenInBrowser"
          :href="openInBrowserHref"
          class="download-btn"
          target="_blank"
          rel="noopener noreferrer"
        >
          在浏览器打开
        </a>
      </div>
      <div v-else-if="isVideo" class="preview-video">
        <div v-if="videoLoading" class="video-loading">
          <div class="loading-spinner"></div>
          <div class="loading-text">视频加载中，请稍候...</div>
        </div>
        <video 
          v-show="!videoLoading"
          ref="videoPlayer"
          :src="videoSrc" 
          controls 
          preload="metadata" 
          playsinline 
          @loadeddata="onVideoLoaded"
          @error="onVideoError"
        />
      </div>
      <div v-else-if="previewFile.is_image" class="preview-image">
        <img :src="imageSrc" :alt="previewFile.name" />
      </div>
      <div v-else-if="previewFile.is_binary" class="preview-binary">
        <p>无法预览二进制文件</p>
        <a :href="`/api/preview/${encodeURIComponent(previewFile.path)}`" class="download-btn" target="_blank">在浏览器打开</a>
      </div>
      <div v-else class="preview-text-wrap">
        <button
          type="button"
          class="preview-copy-btn"
          :disabled="!previewFile?.content"
          @click="onCopyClick"
        >
          {{ copyStateLabel }}
        </button>
        <div class="preview-text-scroller">
          <div class="preview-text-gutter" aria-hidden="true">
            <div v-for="n in lineCount" :key="n" class="preview-line-no">{{ n }}</div>
          </div>
          <pre class="preview-text"><code class="hljs" v-html="highlightedHtml"></code></pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import type { PreviewFile } from '../types'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import cpp from 'highlight.js/lib/languages/cpp'
import 'highlight.js/styles/github.css'

// 只注册需要的语言
hljs.registerLanguage('python', python)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('c++', cpp) // 同时注册 c++ 别名



const copyState = ref<'idle' | 'success' | 'error'>('idle')
const copyStateLabel = computed(() => {
  switch (copyState.value) {
    case 'success':
      return 'Copied!'
    case 'error':
      return 'Copy failed'
    default:
      return 'Copy'
  }
})

const onCopyClick = async () => {
  if (!props.previewFile?.content) return

  try {
    // 优先使用现代 Clipboard API
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(props.previewFile.content)
    } else {
      // 降级方案：使用 document.execCommand
      const textarea = document.createElement('textarea')
      textarea.value = props.previewFile.content
      textarea.style.position = 'fixed' // 避免滚动到页面底部
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    
    copyState.value = 'success'
  } catch (err) {
    console.error('复制失败:', err)
    copyState.value = 'error'
  }

  // 2秒后恢复初始状态
  const timer = setTimeout(() => {
    copyState.value = 'idle'
    clearTimeout(timer)
  }, 2000)
}

const props = defineProps<{
  previewFile: PreviewFile | null
  previewLoading: boolean
  previewError: string
  videoLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'videoLoaded'): void
  (e: 'videoError'): void
}>()

const videoPlayer = ref<HTMLVideoElement | null>(null)

function abortVideoDownload() {
  const el = videoPlayer.value
  if (!el) return

  try {
    // 强制中止当前媒体下载：pause + 清空 src + load
    el.pause()
    el.removeAttribute('src')
    // 某些浏览器会保留 currentSrc，调用 load() 可让其进入空资源状态
    el.load()
  } catch (err) {
    console.warn('abortVideoDownload failed:', err)
  }
}

const onVideoLoaded = () => {
  emit('videoLoaded')
}

const onVideoError = (e: Event) => {
  console.error('视频加载失败:', e)
  emit('videoError')
}

// 只要预览文件切换，若上一个是视频，主动中止旧视频下载，避免后端连接堆积
watch(
  () => props.previewFile,
  (_newFile, oldFile) => {
    if (oldFile) {
      // 判断旧文件是否为视频
      const wasVideo = typeof oldFile.is_video === 'boolean' ? oldFile.is_video : isVideoFileName(oldFile.name)
      if (wasVideo) {
        abortVideoDownload()
      }
    }
  }
)

onBeforeUnmount(() => {
  abortVideoDownload()
})

function isVideoFileName(name: string) {
  const lower = (name || '').toLowerCase()
  return lower.endsWith('.mp4') || lower.endsWith('.webm') || lower.endsWith('.ogg')
}

const isVideo = computed(() => {
  const file = props.previewFile
  if (!file) return false
  // 以服务端标记为准；缺失时用后缀兜底
  if (typeof file.is_video === 'boolean') return file.is_video
  return isVideoFileName(file.name)
})

const videoSrc = computed(() => {
  if (!props.previewFile) return ''
  // 走后端新增的 Range 预览接口，支持拖动进度条/快进
  return `/api/preview/${encodeURIComponent(props.previewFile.path)}`
})

const imageSrc = computed(() => {
  if (!props.previewFile) return ''
  return `/api/download/${encodeURIComponent(props.previewFile.path)}`
})

const openInBrowserHref = computed(() => {
  if (!props.previewFile) return ''
  // 对视频优先走 /api/preview（Range），其它默认走 /api/preview（通常会直接在浏览器打开或下载）
  // 图片走 /api/download 也可以打开，但为保持与二进制一致，这里统一走 preview
  return `/api/preview/${encodeURIComponent(props.previewFile.path)}`
})

const shouldShowOpenInBrowser = computed(() => {
  // 只要预览失败（有 previewError）且存在文件信息，就显示“在浏览器打开”
  return !!props.previewFile && !!props.previewError
})

function guessLangByName(name: string) {
  const lower = name.toLowerCase()
  if (lower.endsWith('.js') || lower.endsWith('.mjs') || lower.endsWith('.cjs')) return 'javascript'
  if (lower.endsWith('.ts') || lower.endsWith('.mts') || lower.endsWith('.cts')) return 'typescript'
  if (lower.endsWith('.vue')) return 'xml'
  if (lower.endsWith('.json')) return 'json'
  if (lower.endsWith('.css')) return 'css'
  if (lower.endsWith('.scss')) return 'scss'
  if (lower.endsWith('.html') || lower.endsWith('.xml')) return 'xml'
  if (lower.endsWith('.md')) return 'markdown'
  if (lower.endsWith('.py')) return 'python'
  // 只支持 cpp/py 高亮，其它都不做高亮（避免把更多语言打进包里）
  if (
    lower.endsWith('.cc') ||
    lower.endsWith('.cpp') ||
    lower.endsWith('.cxx') ||
    lower.endsWith('.hpp') ||
    lower.endsWith('.hxx')
  )
    return 'cpp'
  return ''
}

const lineCount = computed(() => {
  const file = props.previewFile
  if (!file?.content) return 0
  const maxChars = 400_000
  const content = file.content.length > maxChars ? file.content.slice(0, maxChars) : file.content
  // 兼容 \n / \r\n
  return content.split(/\r\n|\n/).length
})

const highlightedHtml = computed(() => {
  const file = props.previewFile
  if (!file?.content) return ''

  const maxChars = 400_000
  const content = file.content.length > maxChars ? file.content.slice(0, maxChars) : file.content

  const lang = guessLangByName(file.name || '')
  try {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(content, { language: lang }).value
    }
    return content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
  } catch {
    return content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
  }
})
</script>

<style scoped>
.preview-error-msg {
  margin-bottom: 1rem;
}

.preview-video {
  position: relative;
}

.video-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  padding: 2rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.loading-text {
  color: #6b7280;
  font-size: 0.9rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>