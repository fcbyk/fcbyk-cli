# fcbykcli 插件 API 文档

## 概述

`fcbykcli.api` 为子命令和插件提供了一组统一的运行时 API。

```python
from fcbykcli.api import CommandContext, pass_command_context
```

## 快速开始

```python
import click

from fcbykcli.api import CommandContext, pass_command_context


@click.command()
@pass_command_context
def hello(ctx: CommandContext) -> None:
    count = int(ctx.state.get("run_count", 0)) + 1
    ctx.state.set("run_count", count)
    click.echo(f"run count: {count}")


def register(cli: click.Group) -> None:
    cli.add_command(hello)
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
from fcbykcli.api import get_private_networks, ensure_port_available, detect_iface_type

networks = get_private_networks()  # 获取局域网 IP 列表
ensure_port_available(8080)  # 检查端口是否可用
iface_type = detect_iface_type("en0")  # 检测网卡类型
```

### 5. Web 服务

```python
from fcbykcli.api import create_spa, R

# 创建 SPA 路由
router = create_spa()

# 统一响应格式
R.success(data={"key": "value"})
R.error(message="Something went wrong")
```

## paths 扩展能力

如果一个插件希望被 `byk paths <plugin>` 展示自己的数据路径，可以注册路径提供器。

```python
from fcbykcli.api import (
    CommandContext, 
    PathItem, 
    pass_command_context,
    register_path_provider
)


def my_plugin_paths(context) -> list[PathItem]:
    return [
        ("数据文件", str(context.command_store("my_plugin").path)),
        ("缓存目录", str(context.paths.plugins_dir / "my_plugin" / "cache")),
    ]


def register(cli):
    cli.add_command(my_plugin)
    register_path_provider("my_plugin", my_plugin_paths)
```

## 别名与守护进程

当前子命令一般不需要直接操作别名系统或守护进程内部实现。这些能力目前仍属于框架内部能力。

如果后续需要对外开放更稳定的 API，建议通过 `fcbykcli.api` 再提供一层公开接口。

## 适合插件解决的问题

- 保存上次输入
- 保存最近一次运行结果
- 记录端口、主机、开关状态
- 保存临时历史记录
- 提供 `paths` 子命令需要展示的数据文件位置
- 启动局域网 Web 服务
- 文件上传下载管理
- 实时聊天室功能
