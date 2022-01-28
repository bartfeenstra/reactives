from typing import Any
from unittest import TestCase

from parameterized import parameterized

from reactives import ReactorController, is_reactive, assert_reactive


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


class IsReactiveTest(TestCase):
    @parameterized.expand([
        (True,),
        (999,),
        (_Reactive,),
        (_NotReactive(),),
        (_NotReactiveWithAttribute(),),
    ])
    def test_with_invalid_reactive(self, reactive: Any) -> None:
        self.assertFalse(is_reactive(reactive))

    def test_with_valid_reactive(self) -> None:
        self.assertTrue(is_reactive(_Reactive()))
