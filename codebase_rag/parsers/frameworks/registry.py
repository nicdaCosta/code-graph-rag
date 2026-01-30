from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from .base import FrameworkHandler

_FRAMEWORK_HANDLERS: dict[str, type[FrameworkHandler]] = {}


def register_framework(name: str, handler_class: type[FrameworkHandler]) -> None:
    _FRAMEWORK_HANDLERS[name] = handler_class


def get_framework_handler(name: str) -> FrameworkHandler | None:
    handler_class = _FRAMEWORK_HANDLERS.get(name)
    if handler_class:
        return handler_class()
    return None


def detect_framework(imports: set[str]) -> list[FrameworkHandler]:
    detected: list[FrameworkHandler] = []
    for name, handler_class in _FRAMEWORK_HANDLERS.items():
        handler = handler_class()
        if handler.detect_framework(imports):
            logger.debug(f"Detected framework: {name}")
            detected.append(handler)
    return detected


def get_all_framework_names() -> list[str]:
    return list(_FRAMEWORK_HANDLERS.keys())


def _register_builtin_frameworks() -> None:
    from .react import ReactFrameworkHandler

    register_framework("react", ReactFrameworkHandler)


_register_builtin_frameworks()
