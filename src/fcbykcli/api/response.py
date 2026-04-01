"""Web API 响应格式化工具。"""

from flask import jsonify
from typing import Any, Tuple


def success(data: Any = None, message: str = "success") -> Tuple[Any, int]:
    """构建成功的 API 响应。"""
    return jsonify({
        "code": 200,
        "message": message,
        "data": data
    }), 200


def error(message: str = "error", code: int = 400, data: Any = None) -> Tuple[Any, int]:
    """构建错误的 API 响应。"""
    return jsonify({
        "code": code,
        "message": message,
        "data": data
    }), code
