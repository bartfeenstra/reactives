from contextlib import contextmanager
from typing import Union

from reactives import ReactorDefinition, ReactorController, Reactive, Reactor, scope


class _DummyReactive:
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


class _AssertCalledReactor:
    def __init__(self):
        self.called = False

    def __call__(self) -> None:
        assert not self.called, 'Failed asserting that a reactor (%s) was called only once.' % self
        self.called = True


@contextmanager
def assert_reactor_called(sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
    reactor = _AssertCalledReactor()
    yield from _assert_reactor(reactor, sut)
    assert reactor.called, 'Failed asserting that a reactor (%s) was called, but it was actually never called at all.' % reactor


class _AssertNotCalledReactor:
    def __call__(self):
        raise AssertionError('Failed asserting that a reactor (%s) was not called.' % self)


@contextmanager
def assert_not_reactor_called(sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
    yield from _assert_reactor(_AssertNotCalledReactor(), sut)


@contextmanager
def assert_scope_empty():
    dependencies = []
    with scope.collect(_DummyReactive(), dependencies):
        yield
    if dependencies:
        raise AssertionError(f'Failed asserting that the reactive scope is empty. Instead it is: {dependencies}')


@contextmanager
def assert_in_scope(dependency: ReactorDefinition):
    dependencies = []
    with scope.collect(_DummyReactive(), dependencies):
        yield
    if dependency not in dependencies:
        raise AssertionError(f'Failed asserting that {dependency} was added to the reactive scope.')
