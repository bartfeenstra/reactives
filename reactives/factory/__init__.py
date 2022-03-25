from __future__ import annotations

from functools import singledispatch
from typing import Optional, Any, TYPE_CHECKING, Type, Union, TypeVar

if TYPE_CHECKING:
    from reactives.factory.type import InstanceAttribute
    from reactives.reactor import ReactorController


T = TypeVar('T')


class UnsupportedReactive(ValueError):
    pass  # pragma: no cover


class Reactive:
    """
    Define a reactive type of any kind.
    """

    react: ReactorController

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def reactive(subject: Optional[Any] = None, **kwargs):
    """
    Transform a type or a value into a reactive type or value.

    Returns
    -------
    Union[Reactive, Type[Reactive], InstanceAttribute, Callable[[Any], Union[Reactive, Type[Reactive], InstanceAttribute]]]

    We cannot type hint the return value as this function is overloaded. As we cannot reliably add overloaded
    declarations across modules, adding a return value type hint here would require all type-checked calling code to
    introduce additional type casts, declarations, or checks just to satisfy type checkers.

    """
    import reactives.factory.function  # noqa: E402,F401
    import reactives.factory.property  # noqa: E402,F401
    import reactives.factory.type  # noqa: E402,F401

    def decorator(subject: Any) -> Union[Reactive, Type[Reactive], InstanceAttribute]:
        return _factor_reactive(subject, **kwargs)
    if subject is None:
        return decorator
    return decorator(subject)


def reactive_factory(reactive_type):
    def decorator(function):
        _factor_reactive.register(reactive_type, function)
        return function
    return decorator


@singledispatch
def _factor_reactive(subject: Optional[Any], **kwargs) -> Union[Reactive, Type[Reactive], InstanceAttribute]:
    raise UnsupportedReactive('%s types cannot be made reactive.' % subject)
