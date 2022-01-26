from functools import singledispatch
from typing import Optional, Any


class UnsupportedReactive(ValueError):
    pass  # pragma: no cover


def reactive(subject: Optional[Any] = None, *args, **kwargs):
    def decorator(subject: Any):
        return reactive_type(subject, *args, **kwargs)
    if subject is None:
        return decorator
    return decorator(subject)


@singledispatch
def reactive_type(subject: Optional[Any], *args, **kwargs) -> None:
    raise UnsupportedReactive('%s types cannot be made reactive.' % subject)


import reactives.reactive.function  # noqa: E402,F401
import reactives.reactive.property  # noqa: E402,F401
import reactives.reactive.type  # noqa: E402,F401
