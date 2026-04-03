# fcbykcli 外部插件开发模板

## 适用场景

这份文档用于指导开发**独立的第三方插件包**（通过 pip 安装）。

- 独立的 Python 包，可发布到 PyPI
- 通过 entry points 自动注册到 fcbyk-cli
- 使用 `fcbykcli.api` 公开 API
- 使用统一状态存储
- 按需接入 `byk paths <plugin>`

## 推荐目录结构

```
my-plugin/
├── pyproject.toml
├── README.md
└── src/
    └── my_plugin/
        ├── __init__.py
        └── command.py
```

- `pyproject.toml` - 包配置，包含 entry points 声明
- `src/my_plugin/` - 插件源代码目录
- `__init__.py` - 包初始化文件
- `command.py` - 插件实现和注册函数

## pyproject.toml 配置

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-plugin"
version = "0.1.0"
description = "My fcbyk-cli plugin"
requires-python = ">=3.10"
dependencies = [
    "fcbyk-cli>=1.0.0",
]

[project.entry-points."fcbyk.plugins"]
my_plugin = "my_plugin.command:register"
```

关键点：
- `[project.entry-points."fcbyk.plugins"]` 声明插件入口
- 格式：`插件名 = "模块路径：register 函数"
- fcbyk-cli 启动时会自动加载所有 `fcbyk.plugins` 分组的 entry points

## 最小可用插件

```python
from __future__ import annotations

import click

from fcbykcli.api import CommandContext, pass_command_context


@click.command(help="示例命令说明。")
@pass_command_context
def my_plugin(ctx: CommandContext) -> None:
    click.echo("my_plugin command")


def register(cli: click.Group) -> str:
    """注册函数，返回插件信息字符串。"""
    cli.add_command(my_plugin)
    return "My Plugin (my_plugin)"

只要安装这个包：

```bash
pip install -e .
```

fcbyk-cli 启动时就会自动加载并注册这个命令。

## 推荐写法

```python
from fcbykcli.api import CommandContext, pass_command_context
```

推荐的命令函数形式：

```python
@click.command()
@pass_command_context
def my_plugin(ctx: CommandContext) -> None:
    ...
```

这样可以直接拿到：

- `ctx.name` - 当前命令名
- `ctx.app` - 应用级上下文（Core 层）
- `ctx.state` - 当前命令专属状态存储（StateStore）
- `ctx.shared_state` - 应用级共享状态存储（StateStore）

## 使用状态存储

如果命令需要保存一点简单数据，优先使用 `ctx.state`。

```python
from __future__ import annotations

import click

from fcbykcli.api import CommandContext, pass_command_context


@click.command()
@click.option("--name", default="world")
@pass_command_context
def my_plugin(ctx: CommandContext, name: str) -> None:
    count = int(ctx.state.get("run_count", 0)) + 1
    ctx.state.update({
        "run_count": count,
        "last_name": name,
    })

    click.echo(f"hello {name}")
    click.echo(f"run count: {count}")
```

默认状态文件路径：`~/.fcbyk-cli/plugins/my_plugin/state.json`

常用方法：

- `ctx.state.get("key", default)`
- `ctx.state.set("key", value)`
- `ctx.state.update({...})`
- `ctx.state.delete("key")`
- `ctx.state.clear()`
- `ctx.state.path`  # Path 对象，指向状态文件

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

- `ctx.app.paths.root_dir` - CLI 根目录
- `ctx.app.paths.config_dir` - 配置目录
- `ctx.app.paths.plugins_dir` - 插件目录
- `ctx.app.paths.logs_dir` - 日志目录
- `ctx.app.paths.runtime_dir` - 运行时目录
- `ctx.app.paths.alias_file` - 别名文件

## 接入 `byk paths <plugin>`

如果某个插件希望向用户展示自己的数据文件、缓存目录、导出目录等路径，可以注册路径提供器。

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
def my_plugin(ctx: CommandContext) -> None:
    click.echo("my_plugin")


def my_plugin_path_items(context) -> list[PathItem]:
    return [
        ("数据文件", str(context.command_store("my_plugin").path)),
        ("缓存目录", str(context.paths.plugins_dir / "my_plugin" / "cache")),
    ]


def register(cli: click.Group) -> None:
    cli.add_command(demo)
    register_path_provider("demo", demo_path_items)
```

这样用户执行 `byk paths my_plugin` 就会看到：

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


@click.command(help="my_plugin 命令说明。")
@click.option("--name", default="world", show_default=True, help="输入名称。")
@click.option("--reset-state", is_flag=True, help="清空本地状态。")
@pass_command_context
def my_plugin(ctx: CommandContext, name: str, reset_state: bool) -> None:
    if reset_state:
        ctx.state.clear()
        click.echo("my_plugin state cleared")
        return

    count = int(ctx.state.get("run_count", 0)) + 1
    ctx.state.update({
        "run_count": count,
        "last_name": name,
    })

    click.echo(f"hello {name}")
    click.echo(f"run count: {count}")
    click.echo(f"state file: {ctx.state.path}")


def my_plugin_path_items(context) -> list[PathItem]:
    return [
        ("数据文件", str(context.command_store("my_plugin").path)),
    ]


def register(cli: click.Group) -> str:
    """注册函数，返回插件信息字符串。"""
    cli.add_command(my_plugin)
    register_path_provider("my_plugin", my_plugin_path_items)
    return "My Plugin (my_plugin)"
```

## 不推荐的写法

- 插件自己手动拼 `~/.fcbyk-cli/...`
- 插件自己直接读写 JSON 文件
- 插件直接依赖大量 `fcbykcli.core.*` 内部实现
- 把大量跨插件数据都塞进一个全局文件

更推荐：

- 用 `ctx.state`
- 用 `ctx.shared_state`
- 用 `ctx.app.paths`
- 用 `register_path_provider()`

## 开发和安装

### 开发模式安装

在插件包根目录执行：

```bash
pip install -e .
```

### 验证安装

```bash
# 查看已安装的插件
byk --version

# 查看你的命令帮助
byk my_plugin --help

# 测试命令功能
byk my_plugin
```

### 发布到 PyPI

```bash
# 构建分发包
python -m build

# 上传到 PyPI
python -m twine upload dist/*
```

## 新增插件后的检查项

1. `byk` 根面板里能看到这个插件
2. `byk <plugin> --help` 能正常输出帮助
3. 如果用了状态存储，状态文件路径是否落到预期目录
4. 如果接了 `paths` 扩展，`byk paths <plugin>` 是否输出正确
5. 如果插件有副作用，是否补了最小测试
6. 插件代码是否符合类型注解规范
7. `pyproject.toml` 中的 entry points 配置是否正确

## 推荐测试示例

```python
from click.testing import CliRunner

from fcbykcli.app import create_cli


def test_my_plugin_command(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    result = runner.invoke(create_cli(), ["my_plugin"])

    assert result.exit_code == 0
```

如果需要验证状态文件：

```python
def test_my_plugin_state(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    runner = CliRunner()
    runner.invoke(create_cli(), ["my_plugin"])

    state_file = tmp_path / ".fcbyk-cli" / "plugins" / "my_plugin" / "state.json"
    assert state_file.exists()
```
