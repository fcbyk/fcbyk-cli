import click

from ..utils import storage

CONFIG_FILE = "fcbyk_config.json"
SECTION = "aliases"


def read_aliases() -> dict:
    """读取别名配置（统一存到 ~/.fcbyk/fcbyk_config.json 的 aliases section）"""
    aliases = storage.load_section(CONFIG_FILE, SECTION, default={})
    return aliases if isinstance(aliases, dict) else {}


def write_aliases(aliases: dict) -> None:
    """写入别名配置（只覆盖 aliases section）"""
    storage.save_section(CONFIG_FILE, SECTION, aliases)


class AliasedGroup(click.Group):
    """支持从 aliases.json 动态解析别名的 Group"""

    def resolve_command(self, ctx, args):
        # 1. 尝试正常解析
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # 如果解析失败，可能是别名
            pass

        # 2. 查别名
        if not args:
            return super().resolve_command(ctx, args)

        cmd_name = args[0]
        aliases = read_aliases()
        actual_cmd_parts = aliases.get(cmd_name)

        if actual_cmd_parts:
            if isinstance(actual_cmd_parts, str):
                actual_cmd_parts = [actual_cmd_parts]

            # 构造新的参数列表：[别名对应的真实命令序列] + [原始剩余参数]
            new_args = actual_cmd_parts + list(args[1:])
            return super().resolve_command(ctx, new_args)

        # 3. 如果没别名，再次尝试（这会抛出正常的 Click 错误）
        return super().resolve_command(ctx, args)


@click.group(help="Manage command aliases")
def alias():
    """管理命令别名"""
    pass


@alias.command("add", help="Add a new alias")
@click.argument("alias_name")
@click.argument("command_parts", nargs=-1, required=True)
@click.pass_context
def add_alias(ctx: click.Context, alias_name: str, command_parts: tuple):
    """添加一个新别名"""
    root_ctx = ctx.find_root()
    root_cmd = root_ctx.command

    # 检查 alias_name 是否是已存在的命令
    if isinstance(root_cmd, click.Group) and root_cmd.get_command(root_ctx, alias_name) is not None:
        click.echo(f"Error: '{alias_name}' is an existing command, cannot be used as an alias.", err=True)
        raise SystemExit(1)

    # 检查命令的第一部分是否是有效命令
    command_name = command_parts[0]
    if not isinstance(root_cmd, click.Group) or root_cmd.get_command(root_ctx, command_name) is None:
        click.echo(f"Error: command '{command_name}' does not exist.", err=True)
        raise SystemExit(1)

    aliases = read_aliases()
    if alias_name in aliases:
        old_cmd = aliases[alias_name]
        if isinstance(old_cmd, list):
            old_cmd = " ".join(old_cmd)
        click.echo(f"Warning: alias '{alias_name}' already exists and points to '{old_cmd}'. Overwriting.")

    aliases[alias_name] = list(command_parts)
    write_aliases(aliases)
    click.echo(f"Alias added: {alias_name} -> {' '.join(command_parts)}")


@alias.command("list", help="List all aliases")
def list_aliases():
    """列出所有别名"""
    from ..cli_support.callbacks import print_aliases
    print_aliases(show_empty=True, leading_newline=False)


@alias.command("remove", help="Remove an alias")
@click.argument("alias_name")
def remove_alias(alias_name: str):
    """移除一个别名"""
    aliases = read_aliases()
    if alias_name not in aliases:
        click.echo(f"Error: alias '{alias_name}' does not exist.", err=True)
        return

    del aliases[alias_name]
    write_aliases(aliases)
    click.echo(f"Alias removed: '{alias_name}'")
