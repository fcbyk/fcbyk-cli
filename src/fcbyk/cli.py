#!/usr/bin/env python3
import click, random, os
from fcbyk import commands, defaults
from fcbyk.utils import storage
from fcbyk.commands.alias import AliasedGroup
from fcbyk.cli_support import (
    version_callback, 
    print_aliases, 
    print_commands,
    banner
)


@click.group(
    cls=AliasedGroup,
    context_settings=dict(
        help_option_names=['-h', '--help']
    ),
    invoke_without_command=True
)
@click.option(
    '--version', '-v', 
    is_flag=True, 
    callback=version_callback, 
    expose_value=False, 
    is_eager=True, 
    help='Show version and exit.'
)
@click.pass_context
def main(ctx):
    # 初始化默认配置
    config_path = storage.get_path(defaults.CONFIG_FILE)
    if not os.path.exists(config_path):
        storage.save_json(config_path, defaults.DEFAULT_CONFIG)

    if ctx.invoked_subcommand is None:
        banner_text = random.choice(banner)
        
        click.secho(banner_text, fg="white", dim=True)
        click.echo(ctx.get_help())      # 帮助信息
        print_aliases()                 # 打印别名，如果有
        print_commands(leading_newline=False, merge_local=True)  # 打印已存脚本，如果有


# 注册子命令
for cmd_name in commands.__all__:
    main.add_command(getattr(commands, cmd_name))


if __name__ == "__main__":
    main()
