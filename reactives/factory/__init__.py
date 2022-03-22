from __future__ import annotations

from functools import singledispatch
from typing import Optional, Any, Callable, TYPE_CHECKING, Type, Union, TypeVar

try:
    from typing import ParamSpec, Protocol, runtime_checkable  # type: ignore
except ImportError:
    from typing_extensions import ParamSpec, Protocol, runtime_checkable  # type: ignore

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


def reactive(subject: Optional[Any] = None, **kwargs) -> Union[Reactive, Type[Reactive], InstanceAttribute, Callable[[Any], Union[Reactive, Type[Reactive], InstanceAttribute]]]:
    import reactives.factory.function  # noqa: E402,F401
    import reactives.factory.property  # noqa: E402,F401
    import reactives.factory.type  # noqa: E402,F401

    def decorator(subject: Any) -> Union[Reactive, Type[Reactive], InstanceAttribute]:
        return _factor_reactive(subject, **kwargs)
    if subject is None:
        return decorator
    return decorator(subject)


class ReactiveFactory(Protocol):
    def __call__(self, subject: Any, **kwargs) -> Union[Reactive, Type[Reactive], InstanceAttribute]:
        pass


ReactiveFactoryT = TypeVar('ReactiveFactoryT', bound=ReactiveFactory)


def reactive_factory(reactive_type: type) -> Callable[[ReactiveFactoryT], ReactiveFactoryT]:
    def decorator(function: ReactiveFactoryT) -> ReactiveFactoryT:
        _factor_reactive.register(reactive_type, function)
        return function
    return decorator


# @todo This does not work for properties, which should be reactive as instance attributes but not as class attributes.
# @todo Compare this to functions, which should be reactive as class methods as well as instance methods.
# @todo Should we allow InstanceAttribute to be returned here?
# @todo Basically, how do we define an attribute as a REACTIVE CLASS attribute and/or a REACTIVE INSTANCE attribute?
# @todo - reactive class methods
# @todo - reactive instance methods
# @todo - properties are reactive as instance attributes only
# @todo WE CAN ALREADY DO THIS
# @todo - If the factory returns Reactive, it's a reactive class attribute
# @todo - If the factory returns InstanceAttribute, it's a reactive instance attribute
# @todo - If the factory returns Reactive & InstanceAttribute, it's a reactive class attribute AND instance attribute.
# @todo
# @todo
@singledispatch
def _factor_reactive(subject: Optional[Any], **kwargs) -> Union[Reactive, Type[Reactive], InstanceAttribute]:
    raise UnsupportedReactive('%s types cannot be made reactive.' % subject)
