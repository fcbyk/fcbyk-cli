# fcbykcli 新架构说明

## 概述

`fcbykcli` 是 `fcbyk-cli` 的新一代 Python 包实现。

- 顶层包名使用 `fcbykcli`
- 项目名称仍然保持 `fcbyk-cli`
- 子命令与基础能力解耦
- 子命令通过自动扫描注册
- 未来插件可以通过统一入口接入
- 持久化按"全局 / 子命令"分层

## 目录结构

```
src/fcbykcli/
├── app.py
├── main.py
├── commands/
├── core/
├── api/
└── web/
```

- `app.py` - 负责装配整个 CLI
- `main.py` - 提供命令入口
- `commands/` - 放子命令实现
- `core/` - 放内部基础实现
- `api/` - 对子命令和未来插件公开的开发入口
- `web/` - 预留给需要局域网 Web 服务的命令复用

## 启动流程

1. `fcbykcli.main:main` 作为命令入口
2. `app.py` 中的 `create_cli()` 创建根命令
3. 运行时按需初始化，包括路径布局、环境信息、日志文件
4. 自动扫描 `fcbykcli.commands.*.command`
5. 如果模块中存在 `register(cli)`，则注册该子命令
6. 再加载 `fcbyk.plugins` entry points 插件

## 命令注册约定

每个子命令目录推荐如下：

```
commands/<name>/
├── __init__.py
└── command.py
```

`command.py` 中提供：

```python
def register(cli):
    cli.add_command(...)
```

当前内置命令：`hello`、`info`、`paths`

## 路径与持久化设计

CLI 的数据根目录：`~/.fcbyk-cli`

- `~/.fcbyk-cli/config` - 放全局级文件（别名文件、共享状态文件）
- `~/.fcbyk-cli/commands/<command>` - 放子命令自己的数据文件
- `~/.fcbyk-cli/logs` - 放日志
- `~/.fcbyk-cli/runtime` - 放运行态文件（pid 等）

默认的重要路径：

- CLI 家目录
- 别名文件：`~/.fcbyk-cli/config/alias.byk.json`
- 日志目录

## 状态存储设计

- 全局共享状态与子命令状态分开
- 子命令默认拥有自己的 `state.json`
- 子命令开发者不需要自己拼路径、读写 JSON、处理原子写入

例如 `hello` 的状态文件：`~/.fcbyk-cli/commands/hello/state.json`

## 公开开发入口

```python
from fcbykcli.api import CommandContext, pass_command_context
```

这是当前新架构中明确面向"命令开发者"的入口。

## 根命令面板

直接执行 `bykr` 时，会展示一个状态面板，当前包含：

- 版本信息
- CLI 家目录
- 别名文件
- 日志目录
- 已注册命令
- 当前别名
- 当前后台进程

## paths 命令

`paths` 命令用于查看位置，而不是管理配置。

### `bykr paths`

默认只显示全局公共路径：

- CLI 家目录
- 别名文件
- 日志目录

### `bykr paths <command>`

只显示该子命令自己注册的路径项。

例如：

```bash
bykr paths hello
```

输出：

```
数据文件：~/.fcbyk-cli/commands/hello/state.json
```

子命令自己决定展示哪些路径项，以及每一项的 label。

## 别名能力

新架构保留了原有别名能力，并且支持：

- 全局别名文件
- 本地别名文件合并
- 危险命令确认
- 嵌套别名路径

当前会读取：

- 全局别名：`~/.fcbyk-cli/config/alias.byk.json`
- 本地别名：当前工作目录下的 `alias.byk.json`、`script.byk.json`

## 守护进程能力

新架构保留了后台守护进程能力，内部使用运行态目录保存进程记录。

目前能力包括：

- 记录 PID
- 列出当前守护进程
- 终止指定 PID 或全部守护进程

## 插件扩展方向

当前已经支持加载 `fcbyk.plugins` entry points。

插件包未来可以通过：

- 提供 `register(cli)` 注册命令
- 使用 `fcbykcli.api` 公开 API 获取运行时上下文

这样插件与主程序之间可以保持清晰边界。
