from unittest import TestCase

from reactives import scope, Reactive
from reactives.reactor import ReactorController


class _NotReactive:
    pass


class _NotReactiveWithAttribute:
    def __init__(self):
        self.react = None


class _Reactive(Reactive):
    def __init__(self):
        self.react = ReactorController()


class CollectTest(TestCase):
    def test_without_dependencies(self) -> None:
        reactive = _Reactive()
        with scope.collect(reactive):
            pass
        self.assertEqual([], reactive.react._dependencies)

    def test_with_dependency(self) -> None:
        reactive = _Reactive()
        dependency = _Reactive()
        with scope.collect(reactive):
            scope.register(dependency)
        self.assertEqual([dependency], reactive.react._dependencies)
