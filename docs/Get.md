## Get 子命令

Get 子命令用于快速获取常用开发工具资源：  
- 默认打开对应工具的官网  
- 也可以直接下载安装包到指定目录  
- 支持列出当前内置支持的资源列表

### 基本功能
- 打开指定资源的官方网站
- 下载指定资源的安装包到本地目录
- 列出当前支持的资源名称及其官网地址

### 当前内置资源

默认内置的资源包括（可能随版本调整）：
- `vscode`：Visual Studio Code
- `py`：Python 安装包

### 基本用法
```bash
fcbyk get [选项] [RESOURCE] [DOWNLOAD_DIR]
```

参数含义：
- `RESOURCE`：资源名称，如 `vscode`、`py`
- `DOWNLOAD_DIR`：配合 `--download` 使用时的下载目录，可省略

### 参数说明

- `-l, --list`  
  列出当前支持的所有资源名称及其官网地址，并退出。

- `-d, --download`  
  以“下载模式”获取资源：  
  - 若提供 `DOWNLOAD_DIR`，则下载到该目录  
  - 若未提供 `DOWNLOAD_DIR`，默认下载到当前目录 `.`  

### 行为说明

1. **列出资源**
```bash
fcbyk get --list
```
会使用表格形式打印所有支持的资源及其官网地址。

2. **打开官网（默认行为）**
```bash
fcbyk get vscode
fcbyk get py
```
在未使用 `--download` 时：
- 会检查资源名是否在支持列表中
- 若存在，则在浏览器中打开其官网

3. **下载安装包**
```bash
# 下载 VSCode 到当前目录
fcbyk get vscode --download

# 下载 Python 安装包到指定目录
fcbyk get py --download D:\Installers
```

下载行为说明：
- 会在必要时自动创建下载目录
- 下载完成后会在终端提示安装包的完整路径

### 注意事项
- 资源列表及下载地址可能随版本更新而变化，若发现下载失败或地址失效，可在 issue 中反馈。
- 下载的安装包可能较大，请确保磁盘空间充足。
- 当前资源列表主要面向 Windows 环境，其他平台可能需要手动调整或自行下载。

