from __future__ import annotations

from functools import singledispatch
from typing import Optional, Any, Callable, TYPE_CHECKING

try:
    from typing import Protocol, runtime_checkable
except ImportError:
    from typing_extensions import Protocol, runtime_checkable  # type: ignore

if TYPE_CHECKING:
    from reactives.reactor import ReactorController


class UnsupportedReactive(ValueError):
    pass  # pragma: no cover


# Protocol's actual metaclass is private but we MUST extend it for our own metaclass to work so we ignore MyPy's errors.
class _ReactiveMeta(type(Protocol)):  # type: ignore
    def __instancecheck__(self, instance) -> bool:
        from reactives.reactor import ReactorController

        return hasattr(instance, 'react') and isinstance(instance.react, ReactorController)


@runtime_checkable
class Reactive(Protocol, metaclass=_ReactiveMeta):
    """
    Define a reactive type of any kind.
    """

    react: ReactorController


def assert_reactive(subject: Any) -> None:
    from reactives.reactor import ReactorController

    if not hasattr(subject, 'react'):
        raise AssertionError(f'{subject} is not reactive: {subject}.react does not exist.')
    if not isinstance(subject.react, ReactorController):
        raise AssertionError(f'{subject} is not reactive: {subject}.react is not an instance of {ReactorController}.')


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
