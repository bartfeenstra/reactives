import functools
from contextlib import contextmanager
from typing import Optional, List, Callable

from reactives.typing import Reactive, ReactorDefinition

_dependencies: Optional[List[ReactorDefinition]] = None


@contextmanager
def collect(dependent: Reactive, dependencies: List[ReactorDefinition]) -> None:
    global _dependencies

    clear(dependent, dependencies)

    # Register the dependent to any existing scope before collecting its own.
    register(dependent)

    # Collect the dependencies.
    original_dependencies = _dependencies
    _dependencies = dependencies
    yield dependencies
    _dependencies = original_dependencies

    # Autowire the dependent to all collected dependencies.
    for dependency in dependencies:
        dependency.react.react_weakref(dependent)


def clear(dependent: Reactive, dependencies: List[ReactorDefinition]):
    for dependency in dependencies:
        dependency.react.shutdown_weakref(dependent)
    dependencies.clear()


def register(dependent: ReactorDefinition) -> None:
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
