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
│   ├── paths.py       # register_path_provider, get_path_provider
│   ├── network.py     # 网络工具函数
│   └── web.py         # Web 服务相关工具
│
├── plugins/           # 内置插件（只依赖 api）
│   ├── lansend/       # LANSend 文件共享插件
│   │   ├── __init__.py
│   │   ├── command.py
│   │   ├── controller.py
│   │   └── service.py
│   └── paths/         # 路径查看插件
│       ├── __init__.py
│       └── command.py
│
├── runtime.py         # 运行时装配（根目录）
├── app.py             # 应用装配
└── main.py            # 程序入口
```

各目录职责：

- `core/` - 定义数据结构和抽象接口（Protocol），无 IO 操作
- `infra/` - 提供具体实现（IO、视图、工厂函数）
- `api/` - 对插件和未来外部插件公开的开发入口
- `plugins/` - 放内置插件实现，每个插件一个独立目录
- `runtime.py` - 运行时装配，注入具体实现
- `app.py` - 装配整个 CLI
- `main.py` - 程序入口点

## 启动流程

1. `fcbykcli.main:main` 作为命令入口
2. `app.py` 中的 `create_cli()` 创建根命令
3. 运行时按需初始化，包括路径布局、环境信息、日志文件
4. 自动扫描 `fcbykcli.plugins.*.command`
5. 如果模块中存在 `register(cli)`，则注册该插件
6. 再加载 `fcbyk.plugins` entry points 外部插件

## 插件注册约定

每个插件目录推荐如下：

```
plugins/<name>/
├── __init__.py
└── command.py
```

`command.py` 中提供：

```python
def register(cli):
    cli.add_command(...)
```

当前内置插件：`lansend`、`paths`

## 路径与持久化设计

CLI 的数据根目录：`~/.fcbyk-cli`

- `~/.fcbyk-cli/config` - 放全局级文件（别名文件、共享状态文件）
- `~/.fcbyk-cli/plugins/<plugin>` - 放插件自己的数据文件
- `~/.fcbyk-cli/logs` - 放日志
- `~/.fcbyk-cli/runtime` - 放运行态文件（PID 等）
- `~/.fcbyk-cli/runtime/daemon` - 放守护进程 PID 文件

默认的重要路径：

- CLI 家目录
- 别名文件：`~/.fcbyk-cli/config/alias.byk.json`
- 日志目录

## 状态存储设计

- 全局共享状态与插件状态分开
- 插件默认拥有自己的 `state.json`
- 插件开发者不需要自己拼路径、读写 JSON、处理原子写入

例如 `lansend` 的状态文件：`~/.fcbyk-cli/plugins/lansend/state.json`

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
            path=self.paths.plugin_file(command_name, filename),
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
from fcbykcli.api import (
    CommandContext,
    pass_command_context,
    get_command_context,
    PathItem,
    PathProvider,
    register_path_provider,
    get_path_provider,
    global_path_items,
    get_private_networks,
    ensure_port_available,
    detect_iface_type,
    create_spa,
    R,
    StateStore,
    start_daemon,
)
```

这是当前新架构中明确面向"插件开发者"的入口。

## 根命令面板

直接执行 `byk` 时，会展示一个状态面板，当前包含：

- 已注册插件
- 版本信息
- 当前别名
- 后台守护进程状态

示例输出：

```
Plugins:
  lansend
  paths

Aliases:
  dev      vite
  build    vite build

Background Daemons:
  ● lansend: PID 4252 (port 8080) [running]
  
  Use 'byk --kill <PID|all>' to stop daemons.
```

## paths 插件

`paths` 插件用于查看位置，而不是管理配置。

### `byk paths`



## 别名能力

新架构保留了原有别名能力，并且支持：

- 全局别名文件
- 本地别名文件合并
- 危险命令确认
- 嵌套别名路径

当前会读取：

- 全局别名：`~/.fcbyk-cli/config/alias.byk.json`
- 本地别名：当前工作目录下的 `alias.byk.json`

## 守护进程能力

新架构保留了后台守护进程能力，内部使用运行态目录保存进程记录。

目前能力包括：

- 记录 PID（保存在 `~/.fcbyk-cli/runtime/daemon/`）
- 列出当前守护进程（通过 `byk` 主面板）
- 终止指定 PID 或所有守护进程（通过 `--kill` 选项）

使用方式：

```bash
# 查看所有后台进程
byk

# 终止单个进程
byk --kill 4252

# 终止所有进程
byk --kill all
```

## 插件扩展方向

当前已经支持加载 `fcbyk.plugins` entry points。

插件包可以通过：

- 提供 `register(cli)` 注册插件
- 使用 `fcbykcli.api` 公开 API 获取运行时上下文

这样插件与主程序之间可以保持清晰边界。

### 内置插件

#### 1. lansend
局域网文件共享服务，支持：
- 文件浏览与下载
- 文件上传（可选密码保护）
- 实时聊天功能
- 后台运行模式

#### 2. paths
路径查看工具，用于显示 CLI 和插件的各种路径配置。
