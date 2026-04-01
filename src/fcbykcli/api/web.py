"""Web SPA 应用创建工具。"""

import logging
from pathlib import Path
from typing import Union, List, Optional


# 禁用 Flask 的日志
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def create_spa(
    entry_html: str,
    static_dir: Union[str, Path],
    page: Optional[List[str]] = None,
):
    """创建单页应用 Flask 实例。
    
    Args:
        entry_html: SPA 入口文件名，如 index.html
        static_dir: 静态文件根目录绝对路径（通常是插件包的 dist 目录）
        page: 前端路由列表，如 ["/admin", "/settings"]
        
    Returns:
        配置好的 Flask 应用实例
    """
    from flask import Flask, send_from_directory, make_response
    
    static_dir = Path(static_dir).resolve()
    assets_dir = static_dir / "assets"
    
    app = Flask(
        __name__,
        static_folder=str(assets_dir),
        static_url_path="/assets"
    )

    # SPA 主入口
    @app.route("/")
    def index():
        response = make_response(send_from_directory(str(static_dir), entry_html))
        # 禁用缓存，防止切换应用时显示旧的 HTML
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # 前端路由 - 统一返回入口主页
    if page:
        for url in page:
            def view(entry_html=entry_html, static_dir=static_dir, u=url):
                response = make_response(send_from_directory(str(static_dir), entry_html))
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
            
            endpoint = f"page_{u.strip('/').replace('/', '_') or 'root'}"
            app.add_url_rule(url, endpoint, view)

    return app
