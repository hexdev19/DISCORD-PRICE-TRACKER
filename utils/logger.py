from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog

from config.settings import settings


_ROOT_DIR = Path(__file__).resolve().parent.parent
_LOG_DIR = _ROOT_DIR / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_MAX_BYTES = 10 * 1024 * 1024
_BACKUP_COUNT = 5


def _component_log_file(name: str) -> Path:
	if name.startswith("bot."):
		return _LOG_DIR / "bot.log"
	if name.startswith("scraper."):
		return _LOG_DIR / "scraper.log"
	if name.startswith("tasks."):
		return _LOG_DIR / "tasks.log"
	if name.startswith("services."):
		return _LOG_DIR / "services.log"
	if name.startswith("db."):
		return _LOG_DIR / "db.log"
	return _LOG_DIR / "app.log"


def _build_console_handler() -> logging.StreamHandler:
	handler = logging.StreamHandler()
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(logging.Formatter("%(message)s"))
	return handler


def _build_file_handler(log_path: Path) -> RotatingFileHandler:
	handler = RotatingFileHandler(
		filename=log_path,
		maxBytes=_MAX_BYTES,
		backupCount=_BACKUP_COUNT,
		encoding="utf-8",
	)
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(logging.Formatter("%(message)s"))
	return handler


_CONSOLE_HANDLER = _build_console_handler()
_FILE_HANDLERS: dict[str, RotatingFileHandler] = {}


def _configure_root_logger() -> None:
	root_logger = logging.getLogger()
	root_logger.setLevel(logging.DEBUG)
	if _CONSOLE_HANDLER not in root_logger.handlers:
		root_logger.addHandler(_CONSOLE_HANDLER)


def _configure_structlog() -> None:
	renderer: structlog.types.Processor
	env = getattr(settings, "ENV", "development")
	if env == "development":
		renderer = structlog.dev.ConsoleRenderer()
	else:
		renderer = structlog.processors.JSONRenderer()

	structlog.configure(
		processors=[
			structlog.processors.TimeStamper(fmt="iso"),
			structlog.stdlib.add_log_level,
			structlog.processors.StackInfoRenderer(),
			structlog.processors.format_exc_info,
			renderer,
		],
		wrapper_class=structlog.stdlib.BoundLogger,
		logger_factory=structlog.stdlib.LoggerFactory(),
		cache_logger_on_first_use=True,
	)


_configure_root_logger()
_configure_structlog()


def _get_or_create_file_handler(name: str) -> RotatingFileHandler:
	file_key = str(_component_log_file(name))
	handler = _FILE_HANDLERS.get(file_key)
	if handler is not None:
		return handler

	handler = _build_file_handler(Path(file_key))
	_FILE_HANDLERS[file_key] = handler
	return handler


def get_logger(name: str) -> structlog.BoundLogger:
	stdlib_logger = logging.getLogger(name)
	stdlib_logger.setLevel(logging.DEBUG)
	stdlib_logger.propagate = False

	file_handler = _get_or_create_file_handler(name)
	if file_handler not in stdlib_logger.handlers:
		stdlib_logger.addHandler(file_handler)
	if _CONSOLE_HANDLER not in stdlib_logger.handlers:
		stdlib_logger.addHandler(_CONSOLE_HANDLER)

	return structlog.get_logger(name)
