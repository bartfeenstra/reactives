from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Any

from reactives import scope, Reactive
from reactives.reactor import Reactor, ReactorController, ResolvableReactorController, resolve_reactor_controller, \
    AssertCallCountReactor, ExpectedCallCount


class _DummyReactive(Reactive):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.react = ReactorController()


def _assert_reactor(reactor: Reactor, sut: ResolvableReactorController) -> Iterator[None]:
    sut = resolve_reactor_controller(sut)
    sut.react(reactor)
    try:
        yield None
    finally:
        sut.shutdown(reactor)


# Ignore the decorator because Mypy falsely flags it as a type violation (https://github.com/python/mypy/issues/11373).
@contextmanager  # type: ignore[misc]
def assert_reactor_called(reactor_controller: ResolvableReactorController, expected_call_count: ExpectedCallCount = 1) -> Iterator[None]:
    reactor_controller = resolve_reactor_controller(reactor_controller)
    reactor = AssertCallCountReactor(reactor_controller, expected_call_count)
    yield from _assert_reactor(reactor, reactor_controller)
    reactor.assert_call_count()


# Ignore the decorator because Mypy falsely flags it as a type violation (https://github.com/python/mypy/issues/11373).
@contextmanager  # type: ignore[misc]
def assert_not_reactor_called(reactor_controller: ResolvableReactorController) -> Iterator[None]:
    reactor_controller = resolve_reactor_controller(reactor_controller)
    yield from _assert_reactor(AssertCallCountReactor(reactor_controller, 0), reactor_controller)


@contextmanager
def assert_scope_empty() -> Iterator[None]:
    reactive = _DummyReactive()
    with scope.collect(reactive):
        yield
    if reactive.react._dependencies:
        raise AssertionError(f'Failed asserting that the reactive scope is empty. Instead it is: {reactive.react._dependencies}')


@contextmanager
def assert_in_scope(*dependencies: ResolvableReactorController) -> Iterator[None]:
    reactive = _DummyReactive()
    with scope.collect(reactive):
        yield
    for dependency in dependencies:
        if resolve_reactor_controller(dependency) not in reactive.react._dependencies:
            raise AssertionError(f'Failed asserting that {dependency} was added to the reactive scope.')
