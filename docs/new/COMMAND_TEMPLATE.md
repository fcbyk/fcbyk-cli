# fcbykcli 子命令开发模板

## 适用场景

这份文档用于快速新增一个 `fcbykcli` 子命令。

- 命令自动注册
- 使用 `fcbykcli.api` 公开 API
- 使用统一状态存储
- 按需接入 `bykr paths <command>`

## 推荐目录结构

```text
commands/<name>/
├── __init__.py
└── command.py
```

- `__init__.py` - 可以为空，主要用于把目录作为 Python 包
- `command.py` - 放命令实现和注册函数

## 最小可用模板

```python
from __future__ import annotations

import click

from fcbykcli.api import CommandContext, pass_command_context


@click.command(help="示例命令说明。")
@pass_command_context
def demo(ctx: CommandContext) -> None:
    click.echo("demo command")


def register(cli: click.Group) -> None:
    cli.add_command(demo)
```

只要放到：

```
commands/demo/command.py
```

主程序就会自动扫描并注册这个命令。

## 推荐写法

```python
from fcbykcli.api import CommandContext, pass_command_context
```

推荐的命令函数形式：

```python
@click.command()
@pass_command_context
def demo(ctx: CommandContext) -> None:
    ...
```

这样可以直接拿到：

- `ctx.name` - 当前命令名
- `ctx.app` - 应用级上下文
- `ctx.state` - 当前命令专属状态存储
- `ctx.shared_state` - 应用级共享状态存储

## 使用状态存储

如果命令需要保存一点简单数据，优先使用 `ctx.state`。

```python
from __future__ import annotations

import click

from fcbykcli.api import CommandContext, pass_command_context


@click.command()
@click.option("--name", default="world")
@pass_command_context
def demo(ctx: CommandContext, name: str) -> None:
    count = int(ctx.state.get("run_count", 0)) + 1
    ctx.state.update({
        "run_count": count,
        "last_name": name,
    })

    click.echo(f"hello {name}")
    click.echo(f"run count: {count}")
```

默认状态文件路径：`~/.fcbyk-cli/commands/demo/state.json`

常用方法：

- `ctx.state.get("key", default)`
- `ctx.state.set("key", value)`
- `ctx.state.update({...})`
- `ctx.state.delete("key")`
- `ctx.state.clear()`
- `ctx.state.path`

## 使用共享状态

如果某段轻量数据需要给多个命令共用：

```python
ctx.shared_state.get("token")
ctx.shared_state.set("token", "xxx")
```

适合场景：

- 多个命令都要用的轻量开关
- 简单共享标记
- 不适合放到某个单独命令目录里的小数据

## 读取路径

优先从 `ctx.app.paths` 读取。

```python
click.echo(ctx.app.paths.root_dir)
click.echo(ctx.app.paths.alias_file)
click.echo(ctx.app.paths.logs_dir)
```

常用路径：

- `ctx.app.paths.root_dir`
- `ctx.app.paths.config_dir`
- `ctx.app.paths.commands_dir`
- `ctx.app.paths.logs_dir`
- `ctx.app.paths.runtime_dir`
- `ctx.app.paths.alias_file`

## 接入 `bykr paths <command>`

如果某个命令希望向用户展示自己的数据文件、缓存目录、导出目录等路径，可以注册路径提供器。

```python
from __future__ import annotations

import click

from fcbykcli.api import (
    CommandContext, 
    PathItem, 
    pass_command_context,
    register_path_provider
)


@click.command()
@pass_command_context
def demo(ctx: CommandContext) -> None:
    click.echo("demo")


def demo_path_items(context) -> list[PathItem]:
    return [
        ("数据文件", str(context.command_store("demo").path)),
        ("缓存目录", str(context.paths.command_dir("demo") / "cache")),
    ]


def register(cli: click.Group) -> None:
    cli.add_command(demo)
    register_path_provider("demo", demo_path_items)
```

这样用户执行 `bykr paths demo` 就会看到：

```
数据文件：...
缓存目录：...
```

注意：

- 路径 label 由命令自己定义
- 路径 value 由命令自己定义
- `paths` 命令只负责统一输出

## 推荐的命令模板

```python
from __future__ import annotations

import click

from fcbykcli.api import (
    CommandContext, 
    PathItem, 
    pass_command_context,
    register_path_provider
)


@click.command(help="demo 命令说明。")
@click.option("--name", default="world", show_default=True, help="输入名称。")
@click.option("--reset-state", is_flag=True, help="清空本地状态。")
@pass_command_context
def demo(ctx: CommandContext, name: str, reset_state: bool) -> None:
    if reset_state:
        ctx.state.clear()
        click.echo("demo state cleared")
        return

    count = int(ctx.state.get("run_count", 0)) + 1
    ctx.state.update({
        "run_count": count,
        "last_name": name,
    })

    click.echo(f"hello {name}")
    click.echo(f"run count: {count}")
    click.echo(f"state file: {ctx.state.path}")


def demo_path_items(context) -> list[PathItem]:
    return [
        ("数据文件", str(context.command_store("demo").path)),
    ]


def register(cli: click.Group) -> None:
    cli.add_command(demo)
    register_path_provider("demo", demo_path_items)
```

## 不推荐的写法

- 子命令自己手动拼 `~/.fcbyk-cli/...`
- 子命令自己直接读写 JSON 文件
- 子命令直接依赖大量 `fcbykcli.core.*` 内部实现
- 把大量跨命令数据都塞进一个全局文件

更推荐：

- 用 `ctx.state`
- 用 `ctx.shared_state`
- 用 `ctx.app.paths`
- 用 `register_path_provider()`

## 新增命令后的检查项

1. `bykr` 根面板里能看到这个命令
2. `bykr <command> --help` 能正常输出帮助
3. 如果用了状态存储，状态文件路径是否落到预期目录
4. 如果接了 `paths` 扩展，`bykr paths <command>` 是否输出正确
5. 如果命令有副作用，是否补了最小测试

## 推荐测试示例

```python
from click.testing import CliRunner

from fcbykcli.app import create_cli


def test_demo_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(create_cli(), ["demo"])

    assert result.exit_code == 0
```

如果需要验证状态文件：

```python
def test_demo_state(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    runner.invoke(create_cli(), ["demo"])

    state_file = tmp_path / ".fcbyk-cli" / "commands" / "demo" / "state.json"
    assert state_file.exists()
```
