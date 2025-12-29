import click
import json
import requests
from fcbyk.cli_support.output import show_config
from fcbyk.utils.config import get_config_path, save_config, get_effective_config

config_file = get_config_path('fcbyk', 'openai.json')

default_config = {
    'model': 'deepseek-chat',
    'base_url': 'https://api.deepseek.com',
    'api_key': None,
    'stream': False,
}

def chat_api(messages, model, api_key, base_url, stream=False, timeout=30):
    url = base_url.rstrip('/') + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, stream=stream, timeout=timeout)
        
        if not stream:
            # 非流式模式：直接返回完整响应
            try:
                resp.raise_for_status()
                data = resp.json()
                if 'error' in data:
                    print(f"[API错误] {data['error'].get('message', str(data['error']))}")
                    return None
                return data
            except requests.HTTPError as e:
                try:
                    err = resp.json()
                    print(f"[HTTP错误] {err.get('error', {}).get('message', str(err))}")
                except Exception:
                    print(f"[HTTP错误] {e}")
                return None
            except Exception as e:
                print(f"[响应解析错误] {e}")
                return None
        else:
            # 流式模式：返回生成器
            def stream_generator():
                try:
                    for line in resp.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]
                                if data.strip() == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if 'error' in chunk:
                                        print(f"[API错误] {chunk['error'].get('message', str(chunk['error']))}")
                                        return
                                    yield chunk
                                except Exception as e:
                                    print(f"[流式解析错误] {e}")
                                    continue
                except Exception as e:
                    print(f'[流式读取异常] {e}')
            
            return stream_generator()
            
    except requests.Timeout:
        print('[请求超时] 请检查网络或稍后重试。')
        return None
    except requests.ConnectionError:
        print('[网络错误] 无法连接到API服务器。')
        return None
    except Exception as e:
        print(f'[请求异常] {e}')
        return None

def get_reply_from_response(response, stream=False):
    if not stream:
        try:
            reply = response['choices'][0]['message']['content']
            print('\033[94mAI：\033[0m', reply)
            return reply
        except Exception as e:
            if isinstance(response, dict) and 'error' in response:
                print(f"[API错误] {response['error'].get('message', str(response['error']))}")
            else:
                print(f'[响应内容异常] {e}')
            return ''
    else:
        reply = ''
        try:
            print('\033[94mAI：\033[0m', end='', flush=True)
            for chunk in response:
                delta = chunk['choices'][0]['delta'].get('content', '')
                print(delta, end='', flush=True)
                reply += delta
            print()
        except Exception as e:
            print(f'[流式响应异常] {e}')
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

        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a helpful assistant. Respond in plain text suitable for a console environment. "
                    "Avoid using Markdown, code blocks, or any rich formatting. Use simple line breaks and spaces for alignment."
                )
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
                response = chat_api(
                    messages,
                    effective_config['model'],
                    effective_config['api_key'],
                    effective_config['base_url'],
                    effective_config['stream']
                )
                if response is None:
                    click.echo('请求失败，请检查网络或API Key配置。')
                    continue
                reply = get_reply_from_response(response, effective_config['stream'])
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