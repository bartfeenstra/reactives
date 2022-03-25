from contextlib import contextmanager
from typing import Union, Iterator, Optional, overload, Any, ContextManager

from reactives import scope
from reactives.factory import Reactive
from reactives.reactor import Reactor, ReactorController, ResolvableReactorController, resolve_reactor_controller


class _DummyReactive(Reactive):
    def __init__(self):
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


class _AssertCalledReactor:
    def __init__(self):
        self.called = False

    def __call__(self) -> None:
        assert not self.called, 'Failed asserting that a reactor (%s) was called only once.' % self
        self.called = True


@overload
def assert_reactor_called() -> ContextManager[Reactor]:
    pass


@overload
def assert_reactor_called(sut: Union[Reactive, ReactorController]) -> ContextManager[None]:
    pass


# Ignore the decorator because Mypy falsely flags it as a type violation (https://github.com/python/mypy/issues/11373).
@contextmanager  # type: ignore
def assert_reactor_called(sut: Any = None) -> Iterator[Optional[Reactor]]:
    reactor = _AssertCalledReactor()
    yield from _assert_reactor(reactor, sut)
    assert reactor.called, 'Failed asserting that a reactor (%s) was called, but it was actually never called at all.' % reactor


class AssertNotCalledReactor:
    def __call__(self):
        raise AssertionError('Failed asserting that a reactor (%s) was not called.' % self)


@overload
def assert_not_reactor_called() -> ContextManager[Reactor]:
    pass


@overload
def assert_not_reactor_called(sut: ResolvableReactorController) -> ContextManager[None]:
    pass


@contextmanager  # type: ignore
def assert_not_reactor_called(sut: Optional[ResolvableReactorController] = None) -> Iterator[Optional[Reactor]]:
    yield from _assert_reactor(AssertNotCalledReactor(), sut)


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
