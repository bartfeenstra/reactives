from unittest import TestCase

from reactives.factory import reactive, UnsupportedReactive


class ReactiveTest(TestCase):
    def test_with_unsupported_reactive(self) -> None:
        with self.assertRaises(UnsupportedReactive):
            reactive(999)
