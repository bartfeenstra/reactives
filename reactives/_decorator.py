from __future__ import annotations

from typing import Any, Dict


class Decorator:
    __module__: str
    __name__: str
    __qualname__: str
    __doc__: str | None
    __annotations__: Dict[str, Any]
