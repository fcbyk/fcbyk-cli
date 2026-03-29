"""CLI 命令回调函数"""
import click
from fcbyk.cli_support.output import get_display_width, pad_display_text


def get_version():
    """获取版本号"""
    try:
        from importlib import metadata
        return metadata.version("fcbyk-cli")
    except Exception:
        try:
            import pkg_resources
            return pkg_resources.get_distribution("fcbyk-cli").version
        except Exception:
            return "unknown"


def version_callback(ctx, param, value):
    """版本号回调，使用 rich 渲染精美界面"""
    if not value or ctx.resilient_parsing:
        return
        
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.padding import Padding
        import sys
        import platform

        console = Console()
        
        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")
        
        table.add_row("Version:", f"[bold green]v{get_version()}[/bold green]")
        table.add_row("Python:", sys.version.split()[0])
        table.add_row("Platform:", platform.platform())
        
        panel = Panel(
            table,
            title="[bold magenta]FCBYK-CLI[/bold magenta]",
            title_align="left",
            border_style="bright_blue",
            expand=False,
            padding=(1, 2)
        )
        
        # 使用 Padding 包裹 Panel 以实现类似 margin 的效果
        # (上下, 左右)
        margin_panel = Padding(panel, (1, 1))
        
        console.print(margin_panel)
    except ImportError:
        # 如果 rich 不可用，回退到普通打印
        click.echo(f"v{get_version()}")
        
    ctx.exit()


def print_aliases(show_empty=False, leading_newline=True):
    """打印别名列表（支持递归分组）"""
    try:
        from fcbyk.commands.alias.cli import load_aliases, collect_all_alias_paths
        aliases = load_aliases(merge_local=True)
        
        if aliases:
            if leading_newline:
                click.echo()
            click.echo("Aliases:")
            
            # 收集所有别名路径
            all_paths = collect_all_alias_paths(aliases)
            
            if not all_paths:
                if show_empty:
                    click.echo("No aliases configured.")
                return
            
            # 计算最大宽度（使用显示宽度而非字符长度）
            max_name_len = max(get_display_width(path) for path in all_paths)
            
            # 按路径排序并打印
            for path in sorted(all_paths):
                # 解析命令字符串和 cwd
                cmd_str, cwd = resolve_alias_by_path(aliases, path)
                if cmd_str:
                    # 如果有 cwd，在命令后添加括号显示
                    display_cmd = cmd_str
                    if cwd:
                        display_cmd += f" (cwd: {cwd})"
                    
                    alias_with_padding = pad_display_text(path, max_name_len, min_spaces=2)
                    click.echo("  {}->  {}".format(alias_with_padding, display_cmd))
            
            click.echo()
        elif show_empty:
            click.echo("No aliases configured.")
    except Exception as e:
        pass


def resolve_alias_by_path(aliases, path):
    """根据路径解析别名
    
    Args:
        aliases: 别名字典
        path: 点号分隔的路径
    
    Returns:
        tuple: (cmd_str, cwd) 或 (None, None)
    """
    parts = path.split('.')
    current = aliases
    
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None, None
        current = current[part]
    
    if isinstance(current, str):
        return current, None
    elif isinstance(current, dict):
        return current.get('cmd', ''), current.get('cwd')
    
    return None, None

