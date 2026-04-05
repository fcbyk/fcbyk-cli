# 后台进程管理

## 概述

CLI 提供后台守护进程管理能力，用于管理各插件以后台方式启动的 Web 服务进程。

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