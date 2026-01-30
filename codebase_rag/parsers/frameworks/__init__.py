from __future__ import annotations

from .base import FrameworkHandler
from .registry import detect_framework, get_framework_handler

__all__ = [
    "FrameworkHandler",
    "detect_framework",
    "get_framework_handler",
]
