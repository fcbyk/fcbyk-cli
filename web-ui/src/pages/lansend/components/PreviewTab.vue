<template>
  <div v-if="previewFile" class="tab-pane preview-pane">
    <div class="preview-content">
      <div v-if="previewLoading" class="preview-loading">加载中...</div>
      <div v-else-if="previewError" class="preview-error">{{ previewError }}</div>
      <div v-else-if="isVideo" class="preview-video">
        <video :src="videoSrc" controls preload="metadata" playsinline />
      </div>
      <div v-else-if="previewFile.is_image" class="preview-image">
        <img :src="`/api/download/${encodeURI(previewFile.path)}`" :alt="previewFile.name" />
      </div>
      <div v-else-if="previewFile.is_binary" class="preview-binary">
        <p>无法预览二进制文件</p>
        <a :href="`/api/download/${previewFile.path}`" class="download-btn" download>下载文件</a>
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
import { computed, ref } from 'vue'
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
}>()

const isVideo = computed(() => {
  const name = (props.previewFile?.name || '').toLowerCase()
  return name.endsWith('.mp4') || name.endsWith('.webm') || name.endsWith('.ogg')
})

const videoSrc = computed(() => {
  if (!props.previewFile) return ''
  // 走后端新增的 Range 预览接口，支持拖动进度条/快进
  return `/api/preview/${encodeURI(props.previewFile.path)}`
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
