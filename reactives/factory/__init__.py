from functools import singledispatch
from typing import Optional, Any, Callable


class UnsupportedReactive(ValueError):
    pass  # pragma: no cover


def reactive(subject: Optional[Any] = None, *args, **kwargs):
    import reactives.factory.function  # noqa: E402,F401
    import reactives.factory.property  # noqa: E402,F401
    import reactives.factory.type  # noqa: E402,F401

    def decorator(subject: Any):
        return _factor_reactive(subject, *args, **kwargs)
    if subject is None:
        return decorator
    return decorator(subject)


def reactive_factory(reactive_type: type) -> Callable:
    def decorator(function: Callable) -> Callable:
        _factor_reactive.register(reactive_type, function)
        return function
    return decorator


@singledispatch
def _factor_reactive(subject: Optional[Any], *args, **kwargs) -> None:
    raise UnsupportedReactive('%s types cannot be made reactive.' % subject)
