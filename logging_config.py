from __future__ import annotations

import importlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_STRUCTLOG_MODULE = None
_CONFIGURED = False


class _FallbackJsonLogger:
    """Minimal JSON logger when structlog is unavailable."""

    def __init__(self, name: str, level: int) -> None:
        self._name = name
        self._level = level
        self._logger = logging.getLogger(name)

    def _emit(self, level_name: str, event: str, **kwargs: Any) -> None:
        level_value = getattr(logging, level_name.upper(), logging.INFO)
        if level_value < self._level:
            return

        payload = {
            **kwargs,
            "event": event,
            "logger": self._name,
            "level": level_name.lower(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._logger.log(level_value, json.dumps(payload))

    def info(self, event: str, **kwargs: Any) -> None:
        self._emit("INFO", event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._emit("DEBUG", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._emit("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._emit("ERROR", event, **kwargs)


def configure_logging() -> None:
    """Configure JSON structured logging for console and file sink."""
    global _STRUCTLOG_MODULE, _CONFIGURED

    if _CONFIGURED:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file_enabled = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
    log_console_enabled = os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true"
    log_file_path = os.getenv("LOG_FILE_PATH", "logs/app.jsonl")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    formatter = logging.Formatter("%(message)s")

    if log_console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if log_file_enabled:
        file_path = Path(log_file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    try:
        _STRUCTLOG_MODULE = importlib.import_module("structlog")
    except ImportError:
        _STRUCTLOG_MODULE = None
        _CONFIGURED = True
        return

    _STRUCTLOG_MODULE.configure(
        processors=[
            _STRUCTLOG_MODULE.contextvars.merge_contextvars,
            _STRUCTLOG_MODULE.processors.add_log_level,
            _STRUCTLOG_MODULE.processors.TimeStamper(fmt="iso", utc=True),
            _STRUCTLOG_MODULE.processors.StackInfoRenderer(),
            _STRUCTLOG_MODULE.processors.format_exc_info,
            _STRUCTLOG_MODULE.processors.JSONRenderer(),
        ],
        wrapper_class=_STRUCTLOG_MODULE.make_filtering_bound_logger(level),
        logger_factory=_STRUCTLOG_MODULE.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def get_logger(name: str):
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    if _STRUCTLOG_MODULE is not None:
        return _STRUCTLOG_MODULE.get_logger(name)
    return _FallbackJsonLogger(name, level)
