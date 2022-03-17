import functools
from contextlib import contextmanager
from typing import Optional, List, Callable, Iterator

from reactives.factory import Reactive

_dependencies: Optional[List[Reactive]] = None


@contextmanager
def collect(dependent: Reactive) -> Iterator[None]:
    global _dependencies

    clear(dependent)

    # Register the dependent to any existing scope before collecting its own.
    register(dependent)

    # Collect the dependencies.
    original_dependencies = _dependencies
    _dependencies = dependent.react._dependencies
    yield
    _dependencies = original_dependencies

    # Autowire the dependent to all collected dependencies.
    for dependency in dependent.react._dependencies:
        dependency.react.react_weakref(dependent)


def clear(dependent: Reactive):
    for dependency in dependent.react._dependencies:
        dependency.react.shutdown(dependent)
    dependent.react._dependencies.clear()


def register(dependent: Reactive) -> None:
    """
    Register a reactive if it's a dependency for another one.
    """
    global _dependencies
    if _dependencies is not None:
        _dependencies.append(dependent)


def register_self(decorated_function: Callable) -> Callable:
    """
    Register the instance a reactive method is bound to (also known as `self`), if it's a dependency for
    another one.
    """

    @functools.wraps(decorated_function)
    def _register_self(self, *args, **kwargs):
        register(self)
        return decorated_function(self, *args, **kwargs)

    return _register_self


@contextmanager
def suspend() -> Iterator[None]:
    global _dependencies
    original_dependencies = _dependencies
    _dependencies = None
    yield
    _dependencies = original_dependencies
