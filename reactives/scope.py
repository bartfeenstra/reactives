from __future__ import annotations

import functools
from contextlib import contextmanager
from typing import Callable, Iterator, TypeVar, MutableSequence

from reactives.reactor import ResolvableReactorController, \
    resolve_reactor_controller, ResolvableReactorControllerT, ReactorController

try:
    from typing_extensions import Concatenate, ParamSpec
except ImportError:  # pragma: no cover
    from typing import Concatenate, ParamSpec  # type: ignore  # pragma: no cover

T = TypeVar('T')
P = ParamSpec('P')

_dependencies: MutableSequence[ReactorController] | None = None


@contextmanager
def collect(dependent: ResolvableReactorController) -> Iterator[None]:
    global _dependencies
    dependent = resolve_reactor_controller(dependent)
    clear(dependent)

    # Collect the dependencies.
    original_dependencies = _dependencies
    _dependencies = dependent._dependencies
    yield
    _dependencies = original_dependencies

    # Autowire the dependent to all collected dependencies.
    for dependency in dependent._dependencies:
        dependency.react_weakref(dependent)


def clear(dependent: ResolvableReactorController) -> None:
    dependent = resolve_reactor_controller(dependent)
    for dependency in dependent._dependencies:
        dependency.shutdown(dependent)
    dependent._dependencies.clear()


def register(dependent: ResolvableReactorController) -> None:
    """
    Register a (resolvable) reactor if it's a dependency for another one.
    """
    global _dependencies
    if _dependencies is not None:
        _dependencies.append(resolve_reactor_controller(dependent))


def register_self(decorated_function: Callable[Concatenate[ResolvableReactorControllerT, P], T]) -> Callable[Concatenate[ResolvableReactorControllerT, P], T]:
    """
    Register the instance a reactive method is bound to (also known as `self`), if it's a dependency for
    another one.
    """

    @functools.wraps(decorated_function)
    def _register_self(_self: ResolvableReactorControllerT, *args: P.args, **kwargs: P.kwargs) -> T:
        register(_self)
        return decorated_function(_self, *args, **kwargs)
    return _register_self
