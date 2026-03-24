from __future__ import annotations

import json
import logging
from typing import Any


class _StructuredLogger:
	def __init__(self, logger: logging.Logger) -> None:
		self._logger = logger

	def debug(self, event: str, **kwargs: Any) -> None:
		self._log(self._logger.debug, event, **kwargs)

	def info(self, event: str, **kwargs: Any) -> None:
		self._log(self._logger.info, event, **kwargs)

	def warning(self, event: str, **kwargs: Any) -> None:
		self._log(self._logger.warning, event, **kwargs)

	def error(self, event: str, **kwargs: Any) -> None:
		self._log(self._logger.error, event, **kwargs)

	def exception(self, event: str, **kwargs: Any) -> None:
		kwargs["exc_info"] = True
		self._log(self._logger.error, event, **kwargs)

	def _log(self, method: Any, event: str, **kwargs: Any) -> None:
		exc_info = kwargs.pop("exc_info", False)
		if kwargs:
			payload = json.dumps(kwargs, default=str, ensure_ascii=True)
			message = f"{event} {payload}"
		else:
			message = event
		method(message, exc_info=exc_info)


def get_logger(name: str) -> _StructuredLogger:
	logger = logging.getLogger(name)
	if not logger.handlers:
		handler = logging.StreamHandler()
		formatter = logging.Formatter(
			"%(asctime)s %(levelname)s %(name)s %(message)s",
			"%Y-%m-%d %H:%M:%S",
		)
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		logger.setLevel(logging.INFO)
		logger.propagate = False

	return _StructuredLogger(logger)
