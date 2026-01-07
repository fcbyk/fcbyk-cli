"""
ai 命令行接口模块

常量:
- CONFIG_FILE: 统一配置文件名
- SECTION: 本命令在统一配置文件中的 section 名
- DEFAULT_CONFIG: 默认配置（model, api_url, api_key, stream）
- SYSTEM_PROMPT: AI 系统提示词（控制输出格式）

函数:
- _print_streaming_chunks(chunks) -> str: 边打印边拼接流式响应
- _chat_loop(config: dict): 聊天主循环
- ai(): Click 命令入口，处理参数和配置
"""

import click
from fcbyk.utils import storage
from fcbyk.cli_support.output import show_dict

from .service import (
    AIService,
    AIServiceError,
    ChatRequest,
    extract_assistant_reply,
)

CONFIG_FILE = "fcbyk_config.json"
SECTION = "ai"

DEFAULT_CONFIG = {
    'model': 'deepseek-chat',
    'api_url': 'https://api.deepseek.com/v1/chat/completions',
    'api_key': None,
    'stream': False,
}

SYSTEM_PROMPT = (
    "You are a helpful assistant. Respond in plain text suitable for a console environment. "
    "Avoid using Markdown, code blocks, or any rich formatting. "
    "Use simple line breaks and spaces for alignment."
)


def _print_streaming_chunks(chunks) -> str:
    reply = ''
    click.secho('AI: ', fg='blue', nl=False)
    for chunk in chunks:
        delta = chunk['choices'][0]['delta'].get('content', '')
        if delta:
            click.echo(delta, nl=False)
            reply += delta
    click.echo('')
    return reply


def _chat_loop(config: dict):
    service = AIService()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    click.secho('Chat started. Type "exit" to quit.', fg='cyan')

    while True:
        try:
            user_input = input('You: ').strip()
        except (EOFError, KeyboardInterrupt):
            click.secho('\nChat ended.', fg='cyan')
            break

        if user_input.lower() == 'exit':
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        req = ChatRequest(
            messages=messages,
            model=config['model'],
            api_key=config['api_key'],
            api_url=config['api_url'],
            stream=bool(config['stream']),
        )

        try:
            resp_or_chunks = service.chat(req)

            if req.stream:
                reply = _print_streaming_chunks(resp_or_chunks)
            else:
                reply = extract_assistant_reply(resp_or_chunks)
                click.secho('AI: ', fg='blue', nl=False)
                click.echo(f' {reply}')

            messages.append({"role": "assistant", "content": reply})

        except AIServiceError as e:
            click.secho(f'Error: {e}', fg='red')
            messages.pop()  # 移除失败的用户消息
        except Exception as e:
            click.secho(f'Unknown error: {e}', fg='red')
            messages.pop()


@click.command(name='ai', help='use openai api to chat in terminal')
@click.option(
    "--config", "-c",
    is_flag=True,
    callback=lambda ctx, param, value: show_dict(
        ctx,
        param,
        value,
        f"config: {storage.get_path(CONFIG_FILE)} / section: {SECTION}",
        storage.load_section(CONFIG_FILE, SECTION, default=DEFAULT_CONFIG),
    ),
    expose_value=False,
    is_eager=True,
    help="show config and exit"
)
@click.option('--model', '-m', help='set model')
@click.option('--api-key', '-k', help='set api key')
@click.option('--api-url', '-u', help='set api url (full url)')
@click.option('--stream', '-s', help='set stream, 0 for false, 1 for true')
@click.pass_context
def ai(ctx, model, api_key, api_url, stream):
    # 读取 section 配置，并用 default 补齐
    config = storage.load_section(CONFIG_FILE, SECTION, default=DEFAULT_CONFIG)

    cli_options = {k: v for k, v in ctx.params.items() if v is not None}

    # CLI 参数覆盖配置
    config_updated = False
    for key, value in cli_options.items():
        if key in DEFAULT_CONFIG:
            # 特殊处理布尔型 stream
            if key == 'stream':
                new_val = str(value).lower() in ['1', 'true']
            else:
                new_val = value
            
            if config.get(key) != new_val:
                config[key] = new_val
                config_updated = True

    # 无参数则进入聊天模式，有参数则保存配置
    if not any([model, api_key, api_url, stream]):
        if not config.get('api_key'):
            click.secho('Error: api_key is not configured. Please set it via --api-key or the config file.', fg='red', err=True)
            ctx.exit(1)

        _chat_loop(config)
    else:
        storage.save_section(CONFIG_FILE, SECTION, config)
        click.secho(f"Config saved to {CONFIG_FILE} section '{SECTION}'.", fg='green')
        ctx.exit()
