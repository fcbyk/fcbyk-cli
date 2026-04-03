# Daemon 后台进程管理

## 概述

CLI 提供后台守护进程管理能力，用于管理各插件以后台方式启动的 Web 服务进程。

当前支持管理的服务包括：
- `lansend`

守护进程管理只做"进程管理"（查看/终止），不会解析业务参数。

### 基本功能
- 查看当前所有后台服务实例（按服务名、PID、端口展示）
- 按 PID 精确终止单个后台实例
- 一次性终止所有后台实例

### 进程来源说明

后台进程通常来自以下命令的 `-D` 选项：

```bash
byk lansend -p 8080 -d ./share -D
```

该命令会：
1. 先在当前终端交互式设置访问密码
2. 输出访问 URL，并复制到剪贴板
3. Web 服务在后台子进程中持续运行
4. 在 `~/.fcbyk-cli/runtime/daemon/` 目录下记录 PID 文件

---

## 基本用法

### 查看后台进程

直接运行 CLI（不带子命令）时，会在状态面板中显示当前所有已知后台服务实例：

```bash
byk
```

示例输出：

```text
Background Daemons:
  ● lansend: PID 4252 (port 8080) [running]
  ● slide:   PID 6896 (port 80)   [running]

  Use 'byk --kill <PID|all>' to stop daemons.
```

状态说明：
- `●` (绿色) - 运行中
- `○` (红色) - 已停止（会自动清理 PID 文件）

---

## 终止后台进程

### 1. 按 PID 终止

```bash
byk --kill 4252
```

可能的输出：

- 正常终止：
  ```text
  lansend(4252) -> terminated
  ```

- 进程已不在运行：
  ```text
  lansend(4252) -> not_running
  ```

- 未找到对应 PID 文件：
  ```text
  No managed process found with PID=4252.
  ```

### 2. 终止所有后台进程

```bash
byk --kill all
```

输出示例：

```text
Processed 2 daemon(s).
```

---

## 典型使用场景

### 1. 交互完再进入后台

以 Lansend 为例：

```bash
byk lansend -p 8080 -d ./share -D
```

流程：
- 先在当前终端交互式设置访问密码
- 输出访问 URL，并复制到剪贴板
- Web 服务在后台子进程中持续运行

此时可以再次运行 `byk` 查看对应的后台实例。

### 2. 一次性启动多个服务并统一管理

```bash
byk lansend -p 8080 -d ./share1 -D
byk lansend -p 8090 -d ./share2 -D
```

查看所有后台服务：

```bash
byk
```

按 PID 精确停止：

```bash
byk --kill 6896
```

终止所有后台服务：

```bash
byk --kill all
```

---

## 注意事项

- 只管理通过 `-D` 选项启动并记录了 PID 文件的进程；手工启动的 Python 进程不会被自动纳入管理。
- 在 Windows 平台下，后台进程会使用"无控制台窗口"的方式启动，避免闪烁黑框。
- Linux/macOS 下会使用 `start_new_session=True` 的方式在新的会话中运行。
- `list_daemons` 会自动检测进程是否仍在运行，并清理已退出进程的 PID 文件。
- 日志文件保存在 `~/.fcbyk-cli/logs/<service-name>.log`。

---

## 技术细节

### PID 文件命名规则

```
~/.fcbyk-cli/runtime/daemon/daemon-<name>-<pid>.json
```

例如：
- `daemon-lansend-4252.json`
- `daemon-lansend-7852.json`

### PID 文件格式

```json
{
  "name": "lansend",
  "pid": 4252,
  "argv": ["/usr/bin/python", "-m", "fcbykcli.main", "lansend", "-p", "8080", ...],
  "created_at": 1234567890.123,
  "log_file": "/Users/coke/.fcbyk-cli/logs/lansend.log",
  "port": 8080
}
```

### 跨平台进程检测

- **Windows**: 使用 `tasklist` 命令检测进程是否存在
- **Linux/macOS**: 使用 `os.kill(pid, 0)` 检测进程是否存在

### 终止方式

- **Windows**: 使用 `taskkill /PID <pid> /T /F` 终止进程树
- **Linux/macOS**: 使用 `SIGTERM` 信号终止进程
