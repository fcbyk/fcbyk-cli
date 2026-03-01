## 🎉 v0.3.0a2 (2026-03-01)

### ♻️ Refactor

- 重命名 CLI 入口函数为main
- 添加别名命令`byk`


### ✨ Features

- 新增 **svc** 子命令，为 web 服务添加后台守护进程支持
- 新增 **config** 子命令，显示应用目录和配置文件路径
- **slide**: 添加扫码登录功能用于本地快速认证
- **scripts**: scripts支持当前目录脚本合并

### 📝 Documentation

- 添加所有子命令添加使用文档(草稿)

### BREAKING CHANGE

- 修改 **lansend** 命令行选项名称
- 重命名`cmd`子命令为`scripts`
- 移除 **lansend** 配置持久化相关选项和逻辑
- 移除 GUI 模块及相关支持

## 🎉 v0.3.0a1 (2026-02-13)

### ♻️ Refactor

- **pick**: 迁移样式从 SCSS 到 Tailwind CSS
- **slide**: 迁移样式，从 SCSS 到 Tailwind
- **lansend**: 样式从 SCSS 迁移到 Tailwind CSS

### ✨ Features

- **cli**: 初始化默认配置文件
- **lansend**: 重构上传功能并集成到文件列表
- **get**: 新增资源获取命令，支持下载和打开官网
- **cmd**: 添加危险命令执行前的检测和确认机制
- **cmd**: 新增可复用命令管理能力
- **alias**: 改进别名添加和显示功能
- **alias**: 支持为多级命令新建别名

### 🐛 Bug Fixes

- **socket**: 去除前端构建的警告

### 🔧 Chores

- 更新 commitizen 配置和笔记文档

## 🎉 v0.2.2 (2026-01-25)

### ✨ Features

- **lansend**: 添加局域网网络测速功能
- **ai**: 添加富文本渲染支持

### 🐛 Bug Fixes

- **lansend**: 修复磁盘根目录分享名称显示问题

### 🎨 Styles

- **lansend**: 改进前端面包屑的样式和交互体验

## 🎉 v0.2.1 (2026-01-22)

### ✨ Features

- **cli**: 增强CLI界面显示效果并添加rich依赖

### 🐛 Bug Fixes

- **pick**: 修复移动端元素溢出导致按钮无法点击

### ♻️ Refactor

- **utils**: 后端提取通用工具函数到独立模块
- **slide**: 统一前后端API响应格式为R对象规范
- **pick**: 提取 mixin 重构样式

### 📝 Documentation

- clarify 0.1.x development phase

## v0.2.0 (2026-01-20)

Initial stabilized release.

## 0.1.x (Initial development phase)

These early releases were part of the initial exploration phase.
APIs and behaviors were unstable, and some versions were unpublished
due to critical issues.