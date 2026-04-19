# bykcli 插件 API 文档

## 概述

`bykcli.api` 为子命令和插件提供了一组统一的运行时 API。

```python
from bykcli.api import CommandContext, pass_command_context
```

## 快速开始

```python
import click

from bykcli.api import CommandContext, pass_command_context


@click.command()
@pass_command_context
def hello(ctx: CommandContext) -> None:
    count = int(ctx.state.get("run_count", 0)) + 1
    ctx.state.set("run_count", count)
    click.echo(f"run count: {count}")


def register(cli: click.Group) -> str:
    cli.add_command(hello)
    return "my-plugin (hello)"
```

## 插件开发指南

### 1. 项目结构

一个标准的 bykcli 插件应包含以下文件：

```
my-plugin/
├── my_plugin/          # 插件代码包
│   ├── __init__.py
│   ├── main.py         # 入口文件，必须包含 register 函数
│   └── commands.py     # 命令实现（可选）
└── pyproject.toml      # 项目配置
```

### 2. 配置 pyproject.toml

在 `pyproject.toml` 中声明插件入口点：

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-plugin"
version = "0.1.0"
description = "bykcli plugin"
requires-python = ">=3.10"

[project.entry-points."bykcli.plugins"]
my-plugin = "my_plugin.main:register"
```

**关键点：**
- 入口点组必须是 `bykcli.plugins`
- 键名是插件名称（用于标识）
- 值是模块路径：`包名.模块名:函数名`
- `register` 函数接收 `click.Group` 对象，返回描述字符串

### 3. 编写 register 函数

`main.py` 中的 `register` 函数负责注册命令：

```python
from __future__ import annotations

import click
from .commands import my_command

def register(cli: click.Group) -> str:
    """注册插件命令到 CLI。
    
    Args:
        cli: CLI 主命令组
        
    Returns:
        插件描述字符串（用于日志输出）
    """
    cli.add_command(my_command)
    return "my-plugin (my_command)"
```

### 4. 实现命令

使用 `@pass_command_context` 装饰器注入上下文：

```python
import click
from bykcli.api import CommandContext, pass_command_context

@click.command(help="我的自定义命令")
@click.option("--name", default="world", help="名称参数")
@pass_command_context
def my_command(ctx: CommandContext, name: str) -> None:
    # 访问命令专属状态
    count = int(ctx.state.get("run_count", 0)) + 1
    ctx.state.set("run_count", count)
    
    # 使用命令专属 logger
    ctx.logger.info("执行命令，name=%s, count=%d", name, count)
    
    click.echo(f"Hello {name}! Run count: {count}")
```

### 5. 安装与使用

```bash
# 进入插件目录
cd my-plugin

# 安装到当前环境
pip install -e .

# 验证插件已加载
byk --help  # 应该能看到你的命令
```

## 公开入口

### `pass_command_context`

装饰器，用于把运行时上下文注入到命令函数中。

### `CommandContext`

插件命令执行时拿到的上下文对象。

- `ctx.name` - 当前命令名
- `ctx.app` - 应用级上下文（Core 层）
- `ctx.state` - 当前命令专属状态存储（StateStore）
- `ctx.shared_state` - 应用级共享状态存储（StateStore）
- `ctx.logger` - 命令专属日志器（自动写入 `{command_name}.log`）

**日志使用说明：**

```python
# 不同级别的日志会自动写入对应的日志文件
ctx.logger.debug("调试信息")      # 详细调试信息
ctx.logger.info("正常信息")       # 一般运行信息
ctx.logger.warning("警告信息")    # 需要注意的情况
ctx.logger.error("错误信息")      # 错误情况
```

日志文件位置：`{logs_dir}/{command_name}.log`

### `get_command_context()`

获取当前应用上下文（用于后台进程启动等场景）。

## 状态存储

`ctx.state` 和 `ctx.shared_state` 都使用 `StateStore` 协议。

- `load() -> dict[str, Any]` - 读取完整状态
- `save(data: dict[str, Any]) -> dict[str, Any]` - 覆盖保存整个状态对象
- `get(key, default=None)` - 读取单个键
- `set(key, value) -> dict[str, Any]` - 设置单个键
- `update(values: dict[str, Any]) -> dict[str, Any]` - 批量更新多个键
- `delete(key) -> dict[str, Any]` - 删除某个键
- `clear() -> dict[str, Any]` - 清空整个状态文件
- `path` - 状态文件的实际路径（Path 对象）

## `ctx.app` 可用能力

### 1. 应用信息

- `ctx.app.app_name`
- `ctx.app.version`
- `ctx.app.environment`

其中 `environment` 中包含：

- Python 版本
- 可执行文件路径
- 平台信息

### 2. 路径布局

`ctx.app.paths` 包含：

- `root_dir`
- `config_dir`
- `plugins_dir`
- `logs_dir`
- `runtime_dir`
- `app_config_file`
- `alias_file`
- `app_log_file`
- `daemon_dir`

### 3. 额外获取存储对象

```python
store = ctx.app.command_store("hello")
shared = ctx.app.shared_store()
```

### 4. 网络工具

```python
from bykcli.api import get_private_networks, ensure_port_available, detect_iface_type

networks = get_private_networks()  # 获取局域网 IP 列表
ensure_port_available(8080)  # 检查端口是否可用
detect_iface_type("en0")  # 检测网卡类型
```

### 5. 守护进程管理

```python
from bykcli.api import start_daemon

# 启动后台守护进程
record = start_daemon(ctx.app, "my-service", ["--port", "8080"])
print(f"Started daemon: PID={record.pid}, Log={record.log_file}")
```

**DaemonRecord 属性：**
- `name` - 守护进程名称
- `pid` - 进程 ID
- `argv` - 启动命令参数
- `created_at` - 创建时间戳
- `log_file` - 日志文件路径
- `port` - 端口号（如果指定）

## 路径展示扩展

如果一个插件希望被 `byk paths <plugin>` 展示自己的数据路径，可以注册路径提供器。

### 核心类型和函数

- **`PathItem`**: 路径项类型，定义为 `tuple[str, str]`（描述, 路径）
- **`PathProvider`**: 路径提供器函数类型，签名为 `Callable[[AppContext], list[PathItem]]`
- **`register_path_provider(command_name, provider)`**: 注册路径提供器
- **`get_path_provider(command_name)`**: 获取已注册的路径提供器
- **`global_path_items(context)`**: 获取全局默认路径列表

### 使用示例

```python
from bykcli.api import (
    CommandContext, 
    PathItem, 
    pass_command_context,
    register_path_provider
)


def my_plugin_paths(context) -> list[PathItem]:
    """返回插件相关的路径列表。
    
    Args:
        context: 应用上下文对象
        
    Returns:
        路径项列表，每项为 (描述, 路径) 元组
    """
    return [
        ("数据文件", str(context.command_store("my_plugin").path)),
        ("缓存目录", str(context.paths.plugins_dir / "my_plugin" / "cache")),
    ]


def register(cli):
    cli.add_command(my_plugin)
    # 注册路径提供器（在 register 函数中调用）
    register_path_provider("my_plugin", my_plugin_paths)
    return "my-plugin (my_plugin)"
```

**使用效果：**

```bash
# 查看所有路径
byk paths

# 查看特定插件的路径
byk paths my_plugin
```

## 完整示例

参考 `example-plugin` 目录下的完整示例：

```python
# demo/hello.py
from __future__ import annotations

import click
from bykcli.api import CommandContext, PathItem, pass_command_context, register_path_provider


@click.command(help="Example subcommand to verify dynamic registration.")
@click.option("--name", default="world", show_default=True, help="The object to greet.")
@click.option("--reset-state", is_flag=True, help="Clear hello's local state.")
@pass_command_context
def hello(ctx: CommandContext, name: str, reset_state: bool) -> None:
    # 使用命令专属 logger（默认写入 hello.log）
    ctx.logger.info("hello command executed with name: %s", name)

    store = ctx.state
    if reset_state:
        ctx.logger.debug("Resetting hello state")
        store.clear()
        click.echo("hello state cleared")
        ctx.logger.info("hello state has been cleared")
        return

    count = int(store.get("run_count", 0)) + 1
    store.update({"run_count": count, "last_name": name})

    click.echo(f"hello {name}")
    click.echo(f"run count: {count}")
    click.echo(f"state file: {store.path}")
    
    # 记录不同级别的日志信息
    ctx.logger.debug("Current run count: %d", count)
    ctx.logger.info("Greeted %s for the %d time(s)", name, count)
    if count > 5:
        ctx.logger.warning("Hello command has been run %d times - consider resetting state", count)
    if count > 10:
        ctx.logger.error("Hello command run count (%d) exceeds recommended limit", count)


def hello_path_items(context) -> list[PathItem]:
    """Return hello-related paths."""
    return [("Data File", str(context.command_store("hello").path))]


# 注册路径提供器
register_path_provider("hello", hello_path_items)
```

```python
# demo/main.py
from __future__ import annotations

import click
from .hello import hello

def register(cli: click.Group) -> str:
    """注册 hello 命令。"""
    cli.add_command(hello)
    return "example-plugin (hello)"
```
