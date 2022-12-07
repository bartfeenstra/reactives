from __future__ import annotations

from contextlib import contextmanager
from typing import Union, Iterator, Optional, overload, Any, ContextManager

from reactives import scope
from reactives.factory import Reactive
from reactives.reactor import Reactor, ReactorController, ResolvableReactorController, resolve_reactor_controller, \
    AssertCallCountReactor, ExpectedCallCount


class _DummyReactive(Reactive):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.react = ReactorController()


@overload
def _assert_reactor(reactor: Reactor, sut: None = None) -> Iterator[Reactor]:
    pass


@overload
def _assert_reactor(reactor: Reactor, sut: ResolvableReactorController) -> Iterator[None]:
    pass


def _assert_reactor(reactor: Reactor, sut: Optional[ResolvableReactorController] = None) -> Iterator[Optional[Reactor]]:
    if sut is not None:
        sut = resolve_reactor_controller(sut)
        sut.react(reactor)
        yield None
        sut.shutdown(reactor)
    else:
        yield reactor


@overload
def assert_reactor_called(expected_call_count: ExpectedCallCount = 1) -> ContextManager[Reactor]:
    pass


@overload
def assert_reactor_called(sut: Union[Reactive, ReactorController], expected_call_count: ExpectedCallCount = 1) -> ContextManager[None]:
    pass


# Ignore the decorator because Mypy falsely flags it as a type violation (https://github.com/python/mypy/issues/11373).
@contextmanager  # type: ignore
def assert_reactor_called(sut: Any = None, expected_call_count: ExpectedCallCount = 1) -> Iterator[Optional[Reactor]]:
    reactor = AssertCallCountReactor(expected_call_count)
    yield from _assert_reactor(reactor, sut)
    reactor.assert_call_count()


@overload
def assert_not_reactor_called() -> ContextManager[Reactor]:
    pass


@overload
def assert_not_reactor_called(sut: ResolvableReactorController) -> ContextManager[None]:
    pass


@contextmanager  # type: ignore
def assert_not_reactor_called(sut: Optional[ResolvableReactorController] = None) -> Iterator[Optional[Reactor]]:
    yield from _assert_reactor(AssertCallCountReactor(0), sut)


@contextmanager
def assert_scope_empty() -> Iterator[None]:
    reactive = _DummyReactive()
    with scope.collect(reactive):
        yield
    if reactive.react._dependencies:
        raise AssertionError(f'Failed asserting that the reactive scope is empty. Instead it is: {reactive.react._dependencies}')


@contextmanager
def assert_in_scope(dependency: Reactive) -> Iterator[None]:
    reactive = _DummyReactive()
    with scope.collect(reactive):
        yield
    if dependency not in reactive.react._dependencies:
        raise AssertionError(f'Failed asserting that {dependency} was added to the reactive scope.')
