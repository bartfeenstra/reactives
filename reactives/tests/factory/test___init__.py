from typing import Any
from unittest import TestCase

from parameterized import parameterized

from reactives.factory import assert_reactive, reactive, Reactive, UnsupportedReactive
from reactives.reactor import ReactorController


class reactive_Test(TestCase):
    def test_with_unsupported_reactive(self) -> None:
        with self.assertRaises(UnsupportedReactive):
            reactive(999)


class _NotReactive:
    pass


class _NotReactiveWithAttribute:
    def __init__(self):
        self.react = None


class _Reactive:
    def __init__(self):
        self.react = ReactorController()


class AssertReactiveTest(TestCase):
    @parameterized.expand([
        (True,),
        (999,),
        (_Reactive,),
        (_NotReactive(),),
        (_NotReactiveWithAttribute(),),
    ])
    def test_with_invalid_reactive(self, reactive: Any) -> None:
        with self.assertRaises(AssertionError):
            assert_reactive(reactive)

    def test_with_valid_reactive(self) -> None:
        assert_reactive(_Reactive())


class ReactiveTest(TestCase):
    @parameterized.expand([
        (True,),
        (999,),
        (_Reactive,),
        (_NotReactive(),),
        (_NotReactiveWithAttribute(),),
    ])
    def test_with_invalid_reactive(self, reactive: Any) -> None:
        self.assertNotIsInstance(reactive, Reactive)

    def test_with_valid_reactive(self) -> None:
        self.assertIsInstance(_Reactive(), Reactive)
