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

export default router

