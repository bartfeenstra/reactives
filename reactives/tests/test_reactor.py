import copy
from typing import Any, MutableSequence

import pytest
from parameterized import parameterized

from reactives import Reactive
from reactives.reactor import ReactorController, resolve_reactor_controller, ExpectedCallCount, _ReactorChain, \
    TriggerOrigin
from reactives.tests import assert_reactor_called, assert_not_reactor_called, AssertCallCountReactor


class _Reactive(Reactive):
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.react = ReactorController()


class OnTriggerReactorController(ReactorController):
    def __init__(self) -> None:
        super().__init__()
        self.tracker: MutableSequence[bool] = []

    def _on_trigger(self) -> None:
        self.tracker.append(True)


class NeverExternalTriggerReactorController(ReactorController):
    def __init__(self) -> None:
        super().__init__()
        self.tracker: MutableSequence[bool] = []

    def _on_trigger(self) -> None:
        raise AssertionError('This reactor controller must never be triggered externally.')


class TestReactorChain:
    def test_trigger_without_reactors(self) -> None:
        reactor_controller = ReactorController()
        sut = _ReactorChain()
        sut.trigger(reactor_controller)

    def test_trigger_with_reactor(self) -> None:
        reactor_controller = ReactorController()
        sut = _ReactorChain()
        with assert_reactor_called(reactor_controller):
            sut.trigger(reactor_controller)

    def test_trigger_with_origin_external(self) -> None:
        reactor_controller_1 = OnTriggerReactorController()
        reactor_controller_2 = OnTriggerReactorController()
        reactor_controller_1.react(reactor_controller_2)
        sut = _ReactorChain()
        with assert_reactor_called(reactor_controller_1):
            with assert_reactor_called(reactor_controller_2):
                sut.trigger(reactor_controller_1, origin=TriggerOrigin.EXTERNAL)
        assert [True] == reactor_controller_1.tracker
        assert [True] == reactor_controller_2.tracker

    def test_trigger_with_origin_internal(self) -> None:
        reactor_controller_1 = NeverExternalTriggerReactorController()
        reactor_controller_2 = OnTriggerReactorController()
        reactor_controller_1.react(reactor_controller_2)
        sut = _ReactorChain()
        with assert_reactor_called(reactor_controller_1):
            with assert_reactor_called(reactor_controller_2):
                sut.trigger(reactor_controller_1, origin=TriggerOrigin.INTERNAL)
        assert [] == reactor_controller_1.tracker
        assert [True] == reactor_controller_2.tracker

    def test_trigger_with_diamond_reactors(self) -> None:
        order_tracker = []
        r_a = _Reactive()
        r_b = _Reactive()
        r_ba = _Reactive()
        r_c = _Reactive()
        r_ca = _Reactive()
        r_d = _Reactive()

        r_a.react(lambda: order_tracker.append('a'))
        r_a.react(r_b)
        r_a.react(r_c)
        r_b.react(lambda: order_tracker.append('b'))
        r_b.react(r_ba)
        r_ba.react(lambda: order_tracker.append('ba'))
        r_ba.react(r_d)
        r_c.react(lambda: order_tracker.append('c'))
        r_c.react(r_ca)
        r_ca.react(lambda: order_tracker.append('ca'))
        r_ca.react(r_d)
        r_d.react(lambda: order_tracker.append('d'))

        sut = _ReactorChain()
        sut.trigger(r_a.react)

        # The reactors are laid out as follows, with all relationships being predefined through reactors.
        #
        #     r_a
        #     / \
        #  r_b   r_c
        #   |     |
        # r_ba   r_ca
        #    \   /
        #     r_d
        assert ['a', 'b', 'c', 'ba', 'ca', 'd'] == order_tracker

    def test_trigger_with_diamond_triggers(self) -> None:
        order_tracker = []
        r_a = _Reactive()
        r_b = _Reactive()
        r_ba = _Reactive()
        r_c = _Reactive()
        r_ca = _Reactive()
        r_d = _Reactive()

        def f_a() -> None:
            order_tracker.append('a')
            r_b.react.trigger()
            r_c.react.trigger()
        r_a.react(f_a)

        def f_b() -> None:
            order_tracker.append('b')
            r_ba.react.trigger()
        r_b.react(f_b)

        def f_ba() -> None:
            order_tracker.append('ba')
            r_d.react.trigger()
        r_ba.react(f_ba)

        def f_c() -> None:
            order_tracker.append('c')
            r_ca.react.trigger()
        r_c.react(f_c)

        def f_ca() -> None:
            order_tracker.append('ca')
            r_d.react.trigger()
        r_ca.react(f_ca)

        def f_d() -> None:
            order_tracker.append('d')
        r_d.react(f_d)

        sut = _ReactorChain()
        sut.trigger(r_a.react)

        # The reactors are laid out as follows, with all relationships being defined through triggers from one reactor
        # to another reactive.
        #
        #     f_a
        #     / \
        #  f_b   f_c
        #   |     |
        # f_ba   f_ca
        #    \   /
        #     f_d
        #
        # 'd' appears in the resolved chain twice. Due to the non-declarative nature of triggers, the 'ba' trigger of
        # 'd' is completed by the time 'ca' is triggered and can trigger 'd' again.
        assert ['a', 'b', 'ba', 'd', 'c', 'ca', 'd'] == order_tracker


class TestReactorController:
    def test___copy__(self) -> None:
        sut = ReactorController()
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    def test_trigger_with_on_trigger(self) -> None:
        sut = OnTriggerReactorController()
        sut.trigger()
        assert [True] == sut.tracker

    def test_trigger_with_on_trigger_with_reactor(self) -> None:
        sut = OnTriggerReactorController()
        sut.react(lambda: sut.tracker.append(False))
        sut.trigger()
        assert [True, False] == sut.tracker

    def test_trigger_without_reactors(self) -> None:
        sut = ReactorController()
        sut.trigger()

    def test_react_with_reactor(self) -> None:
        sut = ReactorController()
        reactor = AssertCallCountReactor(sut)
        sut.react(reactor)
        sut.trigger()
        reactor.assert_call_count()

    def test___call___with_reactor(self) -> None:
        sut = ReactorController()
        reactor = AssertCallCountReactor(sut)
        sut(reactor)
        sut.trigger()
        reactor.assert_call_count()

    def test_shutdown(self) -> None:
        sut = ReactorController()
        reactor_not_called_one = AssertCallCountReactor(sut, 0)
        reactor_not_called_two = AssertCallCountReactor(sut, 0)
        sut.react(reactor_not_called_one, reactor_not_called_two)
        sut.shutdown()
        sut.trigger()
        reactor_not_called_one.assert_call_count()
        reactor_not_called_two.assert_call_count()

    def test_shutdown_with_specified_reactors(self) -> None:
        sut = ReactorController()
        reactor_called = AssertCallCountReactor(sut)
        reactor_not_called = AssertCallCountReactor(sut, 0)
        sut.react(reactor_called, reactor_not_called)
        sut.shutdown(reactor_not_called)
        sut.trigger()
        reactor_called.assert_call_count()
        reactor_not_called.assert_call_count()

    def test_react_weakref_with_method(self) -> None:
        sut = ReactorController()

        class _Raise:
            def _raise(self) -> None:
                AssertCallCountReactor(sut, 0)()
        _raise = _Raise()
        sut.react_weakref(_raise._raise)
        del _raise
        sut.trigger()

    def test_react_weakref(self) -> None:
        sut = ReactorController()
        reactor = AssertCallCountReactor(sut, 0)
        sut.react_weakref(reactor)
        del reactor
        sut.trigger()


class TestResolveReactorController:
    def test_with_reactor_controller(self) -> None:
        reactor_controller = ReactorController()
        resolvable = reactor_controller
        assert reactor_controller == resolve_reactor_controller(resolvable)

    def test_with_reactive(self) -> None:
        reactor_controller = ReactorController()

        class _Reactive(Reactive):
            def __init__(self) -> None:
                super().__init__()
                self.react = reactor_controller
        resolvable = _Reactive()
        assert reactor_controller == resolve_reactor_controller(resolvable)


class TestAssertCallCountReactor:
    @parameterized.expand([
        (0, 0),
        (1, 1),
        (2, 2),
        ((1, 3), 1),
        ((1, 3), 2),
        ((1, 3), 3),
    ])
    def test_assert_call_count_should_pass(self, expected_call_count: ExpectedCallCount, actual_call_count: int) -> None:
        self._assert_call_count(expected_call_count, actual_call_count)

    @parameterized.expand([
        (0, 1),
        (1, 0),
        (1, 2),
        (2, 1),
        (2, 3),
        ((1, 3), 0),
        ((1, 3), 4),
    ])
    def test_assert_call_count_should_raise_error(self, expected_call_count: ExpectedCallCount, actual_call_count: int) -> None:
        with pytest.raises(AssertionError):
            self._assert_call_count(expected_call_count, actual_call_count)

    def _assert_call_count(self, expected_call_count: ExpectedCallCount, actual_call_count: int) -> None:
        reactor_controller = ReactorController()
        sut = AssertCallCountReactor(reactor_controller, expected_call_count)
        for _ in range(0, actual_call_count):
            sut()
        sut.assert_call_count()
