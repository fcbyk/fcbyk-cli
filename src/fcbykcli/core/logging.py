"""统一日志初始化。"""

from __future__ import annotations

import logging

from fcbykcli.core.context import AppContext


def setup_logging(context: AppContext) -> logging.Logger:
    """初始化应用日志。"""

    logger = logging.getLogger("fcbykcli")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(context.paths.app_log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    logger.info("logger initialized")
    return logger
