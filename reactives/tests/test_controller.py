import gc
from unittest import TestCase

from reactives import ReactorController
from reactives.tests import assert_reactor_called, assert_not_reactor_called


class _NotReactive:
    pass


class _NotReactiveWithAttribute:
    def __init__(self):
        self.react = None


class _Reactive:
    def __init__(self):
        self.react = ReactorController()


class ReactorControllerTest(TestCase):
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
        self.assertEquals(['r_a', 'r_b', 'r_c', 'f_ca',
                           'r_d', 'r_da', 'r_e'], order_tracker)

    def test_react_using_shortcut_with_reactor(self) -> None:
        sut = ReactorController()
        with assert_reactor_called() as reactor:
            sut(reactor)
            sut.trigger()

    def test_shutdown(self) -> None:
        sut = ReactorController()
        with assert_reactor_called() as reactor:
            sut.react(reactor)
            sut.trigger()
            sut.shutdown(reactor)
            sut.trigger()

    def test_react_weakref(self) -> None:
        sut = ReactorController()
        reactor = assert_not_reactor_called()
        sut.react_weakref(reactor)
        del reactor
        gc.collect()
        sut.trigger()

    def test_shutdown_weakref(self) -> None:
        sut = ReactorController()
        with assert_reactor_called() as reactor:
            sut.react_weakref(reactor)
            sut.trigger()
            sut.shutdown_weakref(reactor)
            sut.trigger()

    def test_suspend(self) -> None:
        sut = ReactorController()
        with assert_not_reactor_called() as reactor:
            sut.react_weakref(reactor)
            with ReactorController.suspend():
                sut.trigger()
