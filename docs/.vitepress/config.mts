import { defineConfig } from 'vitepress'
import search from './configs/search'
import sidebar from './configs/sidebar'

export default defineConfig({

  title: "FCBYK CLI",

  cleanUrls: true,

  themeConfig: {

    outline: [2, 3],

    sidebar,

    darkModeSwitchLabel: "夜间模式",
    sidebarMenuLabel: "文档",
    returnToTopLabel: "返回顶部",
    outlineTitle: "目录",

    docFooter: {
      prev: '上一篇',
      next: '下一篇'
    },

    search,

    socialLinks: [
      { icon: 'github', link: 'https://github.com/fcbyk/fcbyk-cli' }
    ],
  }

})
