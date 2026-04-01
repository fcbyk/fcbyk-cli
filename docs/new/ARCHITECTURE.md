# fcbykcli 新架构说明

## 概述

`fcbykcli` 是 `fcbyk-cli` 的新一代 Python 包实现。

- 顶层包名使用 `fcbykcli`
- 项目名称仍然保持 `fcbyk-cli`
- 子命令与基础能力解耦
- 子命令通过自动扫描注册
- 未来插件可以通过统一入口接入
- 持久化按"全局 / 子命令"分层
- **Core 与 Infra 分层设计（依赖倒置）**

## 目录结构

```
src/fcbykcli/
├── core/              # 核心层：纯逻辑 + 抽象
│   ├── context.py     # AppContext 数据类
│   ├── environment.py # EnvironmentInfo 数据类
│   ├── persistence.py # PathLayout 数据类
│   ├── state.py       # StateStore Protocol
│   ├── config.py      # ConfigStore Protocol
│   └── errors.py      # CliError 异常
│
├── infra/             # 基础设施层：具体实现
│   ├── persistence.py # build_path_layout, read_json, write_json
│   ├── state.py       # JsonFileStateStore, CommandJsonStateStore
│   ├── config.py      # JsonFileConfigStore
│   ├── aliases.py     # 别名系统实现
│   ├── daemon.py      # 守护进程管理
│   ├── logging.py     # 日志初始化
│   ├── registry.py    # 命令注册
│   └── view.py        # CLI 视图渲染（含 format_version_line）
│
├── api/               # 公开 API（业务层入口）
│   ├── context.py     # CommandContext, pass_command_context
│   └── paths.py       # register_path_provider, get_path_provider
│
├── runtime.py         # 运行时装配（根目录）
├── app.py             # 应用装配
└── commands/          # 子命令（只依赖 api）
```

各目录职责：

- `core/` - 定义数据结构和抽象接口（Protocol），无 IO 操作
- `infra/` - 提供具体实现（IO、视图、工厂函数）
- `api/` - 对子命令和未来插件公开的开发入口
- `runtime.py` - 运行时装配，注入具体实现
- `app.py` - 装配整个 CLI
- `commands/` - 放子命令实现，每个子命令一个独立目录

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

当前内置命令：`hello`、`paths`

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

## Core 与 Infra 分层架构

### 设计原则

**Core 层（纯逻辑 + 抽象）：**
- 只包含数据类（`@dataclass`）
- 定义 Protocol（抽象接口）
- 纯计算逻辑（无 IO、无副作用）

**Infra 层（具体实现）：**
- 提供所有具体实现（带 IO 操作）
- 工厂函数
- 视图渲染
- 运行时装配

**依赖方向：**
```
Infra → Core （✓ 正确）
Core → Infra （✗ 错误）
```

### 示例

**Core 层定义接口：**
```python
# core/state.py
class StateStore(Protocol):
    """状态存储协议。"""
    
    path: Path
    def load(self) -> dict[str, Any]: ...
    def save(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get(self, key: str, default: Any = None) -> Any: ...
```

**Infra 层提供实现：**
```python
# infra/state.py
class JsonFileStateStore:
    """基于 JSON 文件的状态存储实现。"""
    
    def __init__(self, path: Path) -> None:
        self.path = path
    
    def load(self) -> dict[str, Any]:
        data = read_json(self.path, default={})
        return data if isinstance(data, dict) else {}
    
    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        write_json(self.path, data)
        return data
```

**运行时注入：**
```python
# runtime.py
class RuntimeAppContext(AppContext):
    def command_store(self, command_name: str, filename: str = "state.json"):
        return CommandJsonStateStore(
            command_name=command_name,
            path=self.paths.command_file(command_name, filename),
        )
```

### 优势

1. **清晰的职责分离**
   - Core：定义"是什么"（数据结构 + 接口）
   - Infra：定义"怎么做"（具体实现）

2. **依赖倒置原则**
   - 业务层依赖抽象（Protocol）
   - 实现层依赖抽象
   - 核心层独立于实现

3. **易于扩展**
   - 可轻松替换存储后端（JSON → SQLite）
   - 可添加新的 Infra 实现
   - 不影响业务代码

4. **更好的可测试性**
   - Core 层可独立单元测试
   - Infra 层可通过 Mock 测试
   - 业务层可注入测试实现

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
