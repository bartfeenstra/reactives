import copy
import pickle

from reactives._callable import CallableReactorController
from reactives.tests import assert_reactor_called, assert_not_reactor_called


class TestCallableReactorController:
    def test___copy__(self) -> None:
        sut = CallableReactorController()
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    def test___getstate__(self) -> None:
        sut = CallableReactorController()
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        with assert_not_reactor_called(sut):
            with assert_reactor_called(unpickled_sut):
                unpickled_sut.trigger()

    def test_trigger_without_reactors(self) -> None:
        sut = CallableReactorController()
        sut.trigger()

    def test_trigger_with_reactor(self) -> None:
        sut = CallableReactorController()
        with assert_reactor_called(sut):
            sut.trigger()

    def test_on_trigger_call(self) -> None:
        called = False

        def on_trigger() -> None:
            nonlocal called
            called = True
        sut = CallableReactorController(on_trigger_call=on_trigger)
        sut.trigger()
        assert called is True
