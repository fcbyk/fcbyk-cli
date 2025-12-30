/**
 * Pick 页面路由配置
 * 
 * 开发环境：访问路径是 /pick/，所以 base 是 /pick/
 * 生产环境：后端挂载在根目录，base 是 /
 * 
 * 路由：
 * - /  -> 普通抽奖（ItemPick）
 * - /f -> 文件抽奖（FilePick）
 * 
 * 注意：使用 history 模式需要后端支持：
 * - 后端需要配置 / 和 /f 都返回同一个 HTML 文件（index.html）
 * - 或者后端配置将所有路径都重定向到 index.html，让前端路由处理
 */

import { createRouter, createWebHistory } from 'vue-router'
import ItemPick from './ItemPick.vue'
import FilePick from './FilePick.vue'
import Admin from './Admin.vue'
import { fetchInfo } from './api'

// 动态获取 base 路径
// 开发环境：路径包含 /pick/，base 是 /pick/
// 生产环境：路径是根目录，base 是 /
const getBasePath = () => {
  const path = window.location.pathname
  if (path.includes('/pick/')) {
    return '/pick/'
  }
  return '/'
}

const router = createRouter({
  history: createWebHistory(getBasePath()),
  routes: [
    {
      path: '/',
      name: 'item-pick',
      component: ItemPick
    },
    {
      path: '/f',
      name: 'file-pick',
      component: FilePick
    },
    {
      path: '/admin',
      name: 'admin',
      component: Admin
    }
  ]
})

// 缓存启动信息，避免每次路由切换都请求
let cachedInfo: { files_mode: boolean } | null = null
let infoPromise: Promise<{ files_mode: boolean }> | null = null

async function getInfo(): Promise<{ files_mode: boolean }> {
  if (cachedInfo) {
    return cachedInfo
  }
  if (infoPromise) {
    return infoPromise
  }
  infoPromise = fetchInfo()
  cachedInfo = await infoPromise
  return cachedInfo
}

// 路由守卫：根据文件模式进行路由跳转
router.beforeEach(async (to, _from, next) => {
  // 获取当前路径（去除 base 路径）
  const path = to.path
  const basePath = getBasePath()
  // 标准化路径：移除 base 路径前缀
  const normalizedPath = basePath !== '/' ? path.replace(basePath, '') || '/' : path
  
  try {
    const info = await getInfo()
    
    // 如果是文件模式，访问 / 时自动跳转到 /f
    if (normalizedPath === '/' && info.files_mode) {
      next('/f')
      return
    }
    
    // 如果不是文件模式，访问 /f 或 /admin 时跳转到 /
    if ((normalizedPath === '/f' || normalizedPath === '/admin') && !info.files_mode) {
      next('/')
      return
    }
  } catch (error) {
    // 如果获取启动信息失败，对于 /f 和 /admin 路径，默认跳转到 /
    // 因为如果后端不支持文件模式，这些路径不应该存在
    if (normalizedPath === '/f' || normalizedPath === '/admin') {
      next('/')
      return
    }
  }
  
  next()
})

export default router

