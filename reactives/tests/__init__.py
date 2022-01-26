from contextlib import contextmanager
from typing import Union

from reactives import ReactorController, Reactor, Reactive, ReactorDefinition, scope


class _Reactive:
    def __init__(self):
        self.react = ReactorController()


def _assert_reactor(reactor: Reactor, sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
    if sut is not None:
        if not isinstance(sut, ReactorController):
            sut = sut.react
        sut.react(reactor)
        yield None
        sut.shutdown(reactor)
    else:
        yield reactor


@contextmanager
def assert_reactor_called(sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
    def reactor() -> None:
        assert not reactor.called, 'Failed asserting that a reactor (%s) was called only once.' % reactor
        reactor.called = True
    reactor.called = False
    yield from _assert_reactor(reactor, sut)
    assert reactor.called, 'Failed asserting that a reactor (%s) was called, but it was actually never called at all.' % reactor


@contextmanager
def assert_not_reactor_called(sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
    def reactor() -> None:
        raise AssertionError('Failed asserting that a reactor (%s) was not called.' % reactor)
    yield from _assert_reactor(reactor, sut)


@contextmanager
def assert_scope_empty():
    dependencies = []
    with scope.collect(_Reactive(), dependencies):
        yield
    assert dependencies == []


@contextmanager
def assert_in_scope(dependency: ReactorDefinition):
    dependencies = []
    with scope.collect(_Reactive(), dependencies):
        yield
    assert dependency in dependencies
