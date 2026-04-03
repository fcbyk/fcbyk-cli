# Paths 内置插件

默认只显示全局公共路径：

- CLI Home - CLI 家目录
- Alias File - 别名文件
- Logs Directory - 日志目录

### `byk paths`

显示全局路径信息。

### `byk paths <plugin>`

只显示该插件自己注册的路径项。

例如：

```bash
byk paths lansend
```

输出：

```
数据文件：~/.fcbyk-cli/plugins/lansend/state.json
```

插件自己决定展示哪些路径项，以及每一项的 label。

## 如何为你的插件注册路径

在你的插件 command.py 中：

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

def register(cli: click.Group) -> None:
    cli.add_command(my_plugin)
    register_path_provider("my_plugin", my_plugin_paths)
```