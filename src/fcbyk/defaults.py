"""fcbyk 默认配置定义

该字典的结构与 ~/.fcbyk/fcbyk_config.json 完全一致。
"""

CONFIG_FILE = "fcbyk_config.json"

DEFAULT_CONFIG = {
    "ai": {
        "model": "deepseek-chat",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "api_key": None,
        "stream": False,
        "rich": False,
    },
    "aliases": {
        "ls": ["lansend"],
        "run": ["cmd", "run"],
    },
    "lansend": {
        "port": 80,
        "shared_directory": ".",
        "password_flag": False,
        "no_browser": False,
        "un_download": False,
        "un_upload": False,
        "chat": False,
    },
}
