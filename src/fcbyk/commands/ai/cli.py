"""ai 命令行接口模块
处理 click 参数、输入输出、循环
"""

import click

from fcbyk.cli_support.output import show_config
from fcbyk.utils.config import get_config_path, save_config, get_effective_config

from .service import (
    AIService,
    AIServiceError,
    ChatRequest,
    extract_assistant_reply,
)


config_file = get_config_path('fcbyk', 'openai.json')

default_config = {
    'model': 'deepseek-chat',
    'base_url': 'https://api.deepseek.com',
    'api_key': None,
    'stream': False,
}


def _print_streaming_chunks(chunks) -> str:
    """边打印边拼接流式输出"""
    reply = ''
    click.echo('\033[94mAI：\033[0m', nl=False)
    try:
        for chunk in chunks:
            delta = chunk['choices'][0]['delta'].get('content', '')
            if delta:
                click.echo(delta, nl=False)
                reply += delta
        click.echo('')
    except Exception as e:
        click.echo(f"[流式响应异常] {e}")
    return reply


@click.command(name='ai', help='use openai api to chat in terminal')
@click.option(
    "--config", "-c",
    is_flag=True,
    callback=lambda ctx, param, value: show_config(
        ctx, param, value, config_file, default_config
    ),
    expose_value=False,
    is_eager=True,
    help="show config and exit"
)
@click.option('--model', '-m', help='set model')
@click.option('--api-key', '-k', help='set api key')
@click.option('--base-url', '-u', help='set base url')
@click.option('--stream', '-s', help='set stream, 0 for false, 1 for true')
@click.pass_context
def ai(ctx, model, api_key, base_url, stream):
    # CLI 参数字典
    cli_options = ctx.params.copy()
    cli_options.pop('config', None)

    # 获取最终生效配置
    effective_config = get_effective_config(cli_options, config_file, default_config)

    if not any([model, api_key, base_url, stream]):
        # 聊天模式
        if not effective_config['api_key']:
            click.echo('未配置 api_key，请先通过 --api-key 或配置文件设置。')
            return

        service = AIService()

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Respond in plain text suitable for a console environment. "
                    "Avoid using Markdown, code blocks, or any rich formatting. Use simple line breaks and spaces for alignment."
                ),
            }
        ]

        while True:
            try:
                user_input = input('You: ')
                if user_input.strip().lower() == 'exit':
                    break
                if user_input.strip() == '':
                    continue

                messages.append({"role": "user", "content": user_input})

                req = ChatRequest(
                    messages=messages,
                    model=effective_config['model'],
                    api_key=effective_config['api_key'],
                    base_url=effective_config['base_url'],
                    stream=bool(effective_config['stream']),
                )

                try:
                    resp_or_chunks = service.chat(req)
                except AIServiceError as e:
                    click.echo(f"请求失败：{e}")
                    continue

                if req.stream:
                    reply = _print_streaming_chunks(resp_or_chunks)
                else:
                    try:
                        reply = extract_assistant_reply(resp_or_chunks)
                        click.echo('\033[94mAI：\033[0m ' + reply)
                    except Exception as e:
                        click.echo(f"[响应内容异常] {e}")
                        reply = ''

                messages.append({"role": "assistant", "content": reply})

            except KeyboardInterrupt:
                click.echo('\n已退出对话。')
                break
            except Exception as e:
                click.echo(f'[主循环异常] {e}')
                continue

    else:
        # 保存配置模式
        save_config(effective_config, config_file)
        click.echo('config saved')
        ctx.exit()

