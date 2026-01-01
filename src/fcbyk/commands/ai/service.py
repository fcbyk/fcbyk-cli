"""
ai 业务逻辑层
封装与 OpenAI 兼容 Chat Completions 接口的请求、响应解析
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, Generator, Iterable, List, Optional, Union

import requests


JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class ChatRequest:
    messages: List[JsonDict]
    model: str
    api_key: str
    base_url: str
    stream: bool = False
    timeout: int = 30


class AIServiceError(RuntimeError):
    """AI 服务错误（网络、HTTP、协议、API error 等统一封装）"""


class AIService:
    """OpenAI 兼容 Chat Completions 客户端"""

    def __init__(self, session: Optional[requests.Session] = None):
        self._session = session or requests.Session()

    @staticmethod
    def _chat_completions_url(base_url: str) -> str:
        return base_url.rstrip('/') + "/v1/chat/completions"

    def chat(self, req: ChatRequest) -> Union[JsonDict, Iterable[JsonDict]]:
        """
        发起对话请求。

        Returns:
            - stream=False: 返回完整 JSON dict
            - stream=True: 返回可迭代的 chunk（generator）
        """
        if not req.api_key:
            raise AIServiceError("api_key 不能为空")

        url = self._chat_completions_url(req.base_url)
        headers = {
            "Authorization": f"Bearer {req.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": req.model,
            "messages": req.messages,
            "stream": req.stream,
        }

        try:
            resp = self._session.post(
                url,
                headers=headers,
                json=payload,
                stream=req.stream,
                timeout=req.timeout,
            )

            if not req.stream:
                return self._parse_non_stream_response(resp)
            return self._stream_chunks(resp)

        except requests.Timeout as e:
            raise AIServiceError("请求超时，请检查网络或稍后重试") from e
        except requests.ConnectionError as e:
            raise AIServiceError("网络错误：无法连接到API服务器") from e
        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"请求异常：{e}") from e

    def _parse_non_stream_response(self, resp: requests.Response) -> JsonDict:
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            # 尝试解析标准 error
            try:
                err = resp.json()
                message = err.get('error', {}).get('message') or str(err)
            except Exception:
                message = str(e)
            raise AIServiceError(f"HTTP错误：{message}") from e

        try:
            data = resp.json()
        except Exception as e:
            raise AIServiceError(f"响应解析错误：{e}") from e

        if isinstance(data, dict) and 'error' in data:
            message = data['error'].get('message', str(data['error']))
            raise AIServiceError(f"API错误：{message}")

        return data

    def _stream_chunks(self, resp: requests.Response) -> Generator[JsonDict, None, None]:
        """将 SSE data: 行解析为 JSON chunk"""
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            try:
                err = resp.json()
                message = err.get('error', {}).get('message') or str(err)
            except Exception:
                message = str(e)
            raise AIServiceError(f"HTTP错误：{message}") from e

        try:
            for line in resp.iter_lines():
                if not line:
                    continue

                text = line.decode('utf-8', errors='replace')
                if not text.startswith('data: '):
                    continue

                data = text[6:]
                if data.strip() == '[DONE]':
                    break

                try:
                    chunk = json.loads(data)
                except Exception:
                    # 忽略无法解析的 chunk
                    continue

                if isinstance(chunk, dict) and 'error' in chunk:
                    message = chunk['error'].get('message', str(chunk['error']))
                    raise AIServiceError(f"API错误：{message}")

                yield chunk

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"流式读取异常：{e}") from e


def extract_assistant_reply(response: JsonDict) -> str:
    """从非流式响应中提取 assistant 回复文本"""
    return response['choices'][0]['message']['content']


def extract_assistant_reply_from_stream(chunks: Iterable[JsonDict]) -> str:
    """从流式 chunks 中拼接 assistant 回复文本"""
    reply = ""
    for chunk in chunks:
        delta = chunk['choices'][0]['delta'].get('content', '')
        reply += delta
    return reply

