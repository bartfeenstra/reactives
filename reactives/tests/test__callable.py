import copy
import pickle

from reactives._callable import CallableReactorController, CallableDefinition
from reactives.tests import assert_reactor_called, assert_not_reactor_called


class TestCallableReactorController:
    def _callable(self) -> None:
        pass

    def test___copy__(self) -> None:
        callable_definition = CallableDefinition(self._callable)
        sut = CallableReactorController(callable_definition)
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    def test___getstate__(self) -> None:
        callable_definition = CallableDefinition(self._callable)
        sut = CallableReactorController(callable_definition)
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        with assert_not_reactor_called(sut):
            with assert_reactor_called(unpickled_sut):
                unpickled_sut.trigger()

    def test_trigger_without_reactors(self) -> None:
        callable_definition = CallableDefinition(self._callable)
        sut = CallableReactorController(callable_definition)
        sut.trigger()

    def test_trigger_with_reactor(self) -> None:
        callable_definition = CallableDefinition(self._callable)
        sut = CallableReactorController(callable_definition)
        with assert_reactor_called(sut):
            sut.trigger()

    def test_on_trigger_call(self) -> None:

        called = False

        def _callable() -> None:
            nonlocal called
            called = True
        callable_definition = CallableDefinition(_callable, on_trigger_call=True)
        sut = CallableReactorController(callable_definition)
        sut.trigger()
        assert called is True
