import copy
import gc
from unittest import TestCase

from reactives import Reactive
from reactives.reactor import ReactorController, resolve_reactor, resolve_reactor_controller
from reactives.tests import assert_reactor_called, assert_not_reactor_called, AssertNotCalledReactor


class _Reactive(Reactive):
    def __init__(self):
        self.react = ReactorController()


class ReactorControllerTest(TestCase):
    def test___copy__(self) -> None:
        sut = ReactorController()
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    def test_react_without_reactors(self) -> None:
        sut = ReactorController()
        sut.trigger()

    def test_react_with_reactor(self) -> None:
        sut = ReactorController()
        with assert_reactor_called() as reactor:
            sut.react(reactor)
            sut.trigger()

    def test_react_with_diamond_reactors(self) -> None:
        sut = ReactorController()
        with assert_reactor_called() as final_reactor:
            intermediate_reactive_1 = _Reactive()
            intermediate_reactive_2 = _Reactive()
            intermediate_reactive_1.react(final_reactor)
            intermediate_reactive_2.react(final_reactor)
            sut.react(intermediate_reactive_1)
            sut.react(intermediate_reactive_2)
            sut.trigger()

    def test_react_with_intermediate_diamond_reactors(self) -> None:
        order_tracker = []
        r_a = _Reactive()
        r_a.react(lambda: order_tracker.append('r_a'))
        r_b = _Reactive()
        r_b.react(lambda: order_tracker.append('r_b'))
        r_c = _Reactive()
        r_c.react(lambda: order_tracker.append('r_c'))
        r_d = _Reactive()
        r_d.react(lambda: order_tracker.append('r_d'))
        r_da = _Reactive()
        r_da.react(lambda: order_tracker.append('r_da'))
        r_e = _Reactive()
        r_e.react(lambda: order_tracker.append('r_e'))

        r_a.react(r_b)
        r_b.react(r_c)
        r_b.react(r_d)

        # This is the intermediate trigger we are asserting is consolidated into the reactor chain.
        def f_ca():
            order_tracker.append('f_ca')
            r_e.react.trigger()
        r_c.react(f_ca)
        r_d.react(r_da)
        r_da.react(r_e)

        r_a.react.trigger()
        self.assertEqual(['r_a', 'r_b', 'r_c', 'f_ca', 'r_d', 'r_da', 'r_e'], order_tracker)

    def test_react_using_shortcut_with_reactor(self) -> None:
        sut = ReactorController()
        with assert_reactor_called() as reactor:
            sut(reactor)
            sut.trigger()

    def test_shutdown(self) -> None:
        sut = ReactorController()
        with assert_not_reactor_called() as reactor_1:
            with assert_not_reactor_called() as reactor_2:
                sut.react(reactor_1, reactor_2)
                sut.shutdown()
                sut.trigger()

    def test_shutdown_with_specified_reactors(self) -> None:
        sut = ReactorController()
        with assert_reactor_called() as reactor_called:
            with assert_not_reactor_called() as reactor_not_called:
                sut.react(reactor_called, reactor_not_called)
                sut.shutdown(reactor_not_called)
                sut.trigger()

    def test_react_weakref(self) -> None:
        sut = ReactorController()
        reactor = AssertNotCalledReactor()
        sut.react_weakref(reactor)
        del reactor
        gc.collect()
        sut.trigger()

    def test_suspend(self) -> None:
        sut = ReactorController()
        with assert_not_reactor_called() as reactor:
            sut.react_weakref(reactor)
            with ReactorController.suspend():
                sut.trigger()


class ResolveReactorTest(TestCase):
    def test_with_reactor(self) -> None:
        def _reactor() -> None:
            pass
        resolvable = _reactor
        self.assertSequenceEqual((resolvable,), tuple(resolve_reactor(resolvable)))

    def test_with_reactor_controller(self) -> None:
        def _reactor() -> None:
            pass
        resolvable = ReactorController()
        resolvable.react(_reactor)
        self.assertSequenceEqual((_reactor,), tuple(resolve_reactor(resolvable)))

    def test_with_reactive(self) -> None:
        def _reactor() -> None:
            pass

        class _Reactive(Reactive):
            def __init__(self):
                self.react = ReactorController()
        resolvable = _Reactive()
        resolvable.react(_reactor)
        self.assertSequenceEqual((_reactor,), tuple(resolve_reactor(resolvable)))


class ResolveReactorControllerTest(TestCase):
    def test_with_reactor_controller(self) -> None:
        reactor_controller = ReactorController()
        resolvable = reactor_controller
        self.assertEqual(reactor_controller, resolve_reactor_controller(resolvable))

    def test_with_reactive(self) -> None:
        reactor_controller = ReactorController()

        class _Reactive(Reactive):
            def __init__(self):
                self.react = reactor_controller
        resolvable = _Reactive()
        self.assertEqual(reactor_controller, resolve_reactor_controller(resolvable))
