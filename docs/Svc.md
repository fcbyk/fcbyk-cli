## Svc 子命令

Svc 子命令用于统一管理由 fcbyk 各子命令以后台方式启动的 Web 服务进程。

当前支持管理的服务包括：
- `lansend`
- `pick`
- `slide`

Svc 只做“进程管理”（查看/停止），不会解析业务参数。

### 基本功能
- 查看当前所有后台服务实例（按服务名、PID、端口展示）
- 查看某个服务名下的所有实例
- 按服务名停止该服务的所有后台实例
- 按 PID 精确终止单个后台实例

### 进程来源说明

Svc 管理的后台进程通常来自以下命令：

- `fcbyk lansend -D ...`
- `fcbyk pick -D ...`
- `fcbyk slide -D ...`

这些命令内部会使用 `fcbyk.svc.start_service(...)` 以子进程方式启动 Web 服务，
并在 `~/.fcbyk/temp/svc/` 目录下记录 PID 文件。

### 基本用法

```bash
fcbyk svc [子命令] [参数...]
```

直接运行 `fcbyk svc`（不带子命令）时，会显示当前所有已知后台服务实例。

示例：

```text
Current background services:
lansend: PID 4252 (port 8080) [running]
slide:   PID 6896 (port 80)   [running]
Use 'fcbyk svc stop <service>' to stop all processes of a service.
```

### 子命令说明

#### 1. status

```bash
fcbyk svc status
fcbyk svc status <service>
```

- `fcbyk svc status`  
  查看所有已知后台服务实例。

- `fcbyk svc status lansend`  
  仅查看 `lansend` 服务的所有实例。

每一行输出形如：

```text
<name>: PID <pid> (port <port>) [running|stopped]
```

为了避免长期残留的“僵尸 PID 文件”，`status` 会在检测到进程已退出时自动清理对应的 PID 文件。

#### 2. stop

```bash
fcbyk svc stop <service>
```

按服务名停止该服务名下的所有后台实例。例如：

```bash
fcbyk svc stop lansend
```

可能的输出示例：

```text
PID 4252 terminated.
PID 7852 terminated.
```

注意：
- `stop` 的参数必须是服务名（如 `lansend` / `pick` / `slide`），不是 PID
- 若希望按 PID 精确停止单个进程，请使用 `kill` 子命令

#### 3. kill

```bash
fcbyk svc kill <pid>
```

按 PID 精确终止一个后台服务实例。示例：

```bash
fcbyk svc kill 4252
```

可能的输出：

- 正常终止：

  ```text
  PID 4252 (lansend) terminated.
  ```

- 进程已不在运行：

  ```text
  PID 4252 (lansend) already not running.
  ```

- 未找到对应 PID 文件：

  ```text
  No tracked process with PID 4252.
  ```

### 典型使用场景

#### 1. 交互完再进入后台

以 Slide 为例：

```bash
fcbyk slide -p 8080 -D
```

流程：
- 先在当前终端交互式设置访问密码
- 输出访问 URL，并复制到剪贴板
- Web 服务在后台子进程中持续运行

此时可以用：

```bash
fcbyk svc
fcbyk svc status slide
```

查看对应的后台实例。

#### 2. 一次性启动多个服务并统一管理

```bash
fcbyk lansend -p 8080 -d D:\Share -D
fcbyk pick --web -p 8090 -D
fcbyk slide -p 9000 -D
```

查看所有后台服务：

```bash
fcbyk svc
```

按服务名停止：

```bash
fcbyk svc stop lansend
```

按 PID 精确停止：

```bash
fcbyk svc kill 6896
```

### 注意事项

- Svc 只管理通过 `fcbyk.svc` 启动并记录了 PID 文件的进程；  
  手工启动的 Python 进程不会被自动纳入管理。
- 在 Windows 平台下，后台进程会使用“无控制台窗口”的方式启动，避免闪烁黑框；
  Linux/macOS 下会使用 `start_new_session=True` 的方式在新的会话中运行。
- 若发现某些 PID 在 `status` 中长期显示为 `stopped`，可以手动执行 `fcbyk svc status` 来触发清理。 
