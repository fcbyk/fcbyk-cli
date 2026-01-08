"""CLI 命令回调函数"""
import click


def get_version():
    """获取版本号"""
    try:
        from importlib import metadata
        return metadata.version("fcbyk-cli")
    except ImportError:
        try:
            import pkg_resources
            return pkg_resources.get_distribution("fcbyk-cli").version
        except Exception:
            return "unknown"


def version_callback(ctx, param, value):
    """版本号回调"""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"v{get_version()}")
    ctx.exit()


def print_aliases():
    """打印别名列表"""
    try:
        from fcbyk.commands.alias import read_aliases
        aliases = read_aliases()
        if aliases:
            click.echo("\nAliases:")
            for alias_name, command in aliases.items():
                click.echo(f"   {alias_name}   =>   {command}")
            click.echo()
    except Exception:
        pass