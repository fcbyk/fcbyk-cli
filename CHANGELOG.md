## 🎉 v0.3.0-alpha.1 (2026-02-13)

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