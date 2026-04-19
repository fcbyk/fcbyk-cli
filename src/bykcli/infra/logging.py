"""统一日志初始化。"""

from __future__ import annotations

import logging

from bykcli.core.context import AppContext


def _get_log_config(context: AppContext) -> dict:
    """从配置文件读取日志配置。"""
    try:
        config_store = context.config_store()
        logging_config = config_store.get("logging", {})
        if isinstance(logging_config, dict):
            return logging_config
    except Exception:
        pass
    return {}


def setup_logging(context: AppContext) -> logging.Logger:
    """初始化应用日志。
    
    从配置文件读取日志级别和传播设置：
    - logging.level: 日志级别（默认 INFO）
    - logging.separate: 命令日志是否独立（默认 True，不传播到 app.log）
    """
    logger = logging.getLogger("bykcli")
    if logger.handlers:
        return logger

    log_config = _get_log_config(context)
    level_str = log_config.get("level", "INFO").upper()
    separate = log_config.get("separate", True)

    try:
        level = getattr(logging, level_str)
    except AttributeError:
        level = logging.INFO

    logger.setLevel(level)
    handler = logging.FileHandler(context.paths.app_log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    logger.debug("logger initialized (level=%s, separate=%s)", level_str, separate)
    return logger


def create_command_logger(context: AppContext, command_name: str) -> logging.Logger:
    """创建命令专属 logger"""
    logger = logging.getLogger(f"bykcli.{command_name}")
    
    if not logger.handlers:
        log_config = _get_log_config(context)
        level_str = log_config.get("level", "INFO").upper()
        separate = log_config.get("separate", True)

        try:
            level = getattr(logging, level_str)
        except AttributeError:
            level = logging.INFO

        logger.setLevel(level)
        
        log_file = context.paths.logs_dir / f"{command_name}.log"
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        
        logger.propagate = not separate
    
    return logger
