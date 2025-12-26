import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'
import { promises as fs } from 'fs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true })
}

async function copyDir(src, dest) {
  await ensureDir(dest)
  const entries = await fs.readdir(src, { withFileTypes: true })

  for (const entry of entries) {
    const srcPath = resolve(src, entry.name)
    const destPath = resolve(dest, entry.name)

    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath)
    } else if (entry.isFile()) {
      await fs.copyFile(srcPath, destPath)
    }
  }
}

async function flatten() {
  const projectRoot = resolve(__dirname, '..')
  const distDir = resolve(projectRoot, 'dist')
  const pagesDir = resolve(distDir, 'src/pages')
  const staticDir = resolve(distDir, 'static')
  const assetsSrcDir = resolve(distDir, 'assets')
  const assetsDstDir = resolve(staticDir, 'assets')

  try {
    // 确保 dist 存在
    await fs.access(distDir)
  } catch {
    console.error('[flatten-dist] dist 目录不存在，请先运行构建（pnpm build）')
    process.exit(1)
  }

  // 创建 static 目录
  await ensureDir(staticDir)

  // 复制 assets 到 static/assets
  try {
    await copyDir(assetsSrcDir, assetsDstDir)
    console.log(`[flatten-dist] 已复制 assets 到 ${assetsDstDir}`)
  } catch (err) {
    console.warn('[flatten-dist] 复制 assets 目录失败：', err)
  }

  // 处理每个页面的 index.html，生成扁平化的 cmd_xxx.html
  const pageNames = await fs.readdir(pagesDir)

  for (const pageName of pageNames) {
    const pageDir = resolve(pagesDir, pageName)
    const stat = await fs.stat(pageDir)
    if (!stat.isDirectory()) continue

    const htmlPath = resolve(pageDir, 'index.html')
    try {
      await fs.access(htmlPath)
    } catch {
      continue
    }

    let htmlContent = await fs.readFile(htmlPath, 'utf-8')

    // 把像 ../../../assets/xxx、../../assets/xxx 这类路径全部规范为 ./assets/xxx
    htmlContent = htmlContent.replace(
      /(["'(])((?:\.\.\/)+)assets\//g,
      '$1./assets/'
    )

    // 页面的输出文件名：用文件夹名，- 转为 _
    const baseName = pageName.replace(/-/g, '_')
    const flatHtmlPath = resolve(staticDir, `${baseName}.html`)

    await fs.writeFile(flatHtmlPath, htmlContent, 'utf-8')
    console.log(`[flatten-dist] 已生成 ${flatHtmlPath}`)
  }

  console.log('[flatten-dist] 扁平化处理完成')
}

flatten().catch(err => {
  console.error('[flatten-dist] 执行失败：', err)
  process.exit(1)
})


