from reactives import scope, Reactive
from reactives.reactor import ReactorController


class _NotReactive:
    pass


class _NotReactiveWithAttribute:
    def __init__(self) -> None:
        self.react = None


class _Reactive(Reactive):
    def __init__(self) -> None:
        super().__init__()
        self.react = ReactorController()


class TestCollect:
    def test_without_dependencies(self) -> None:
        reactive = _Reactive()
        with scope.collect(reactive):
            pass
        assert [] == reactive.react._dependencies

    def test_with_dependency(self) -> None:
        reactive = _Reactive()
        dependency = _Reactive()
        with scope.collect(reactive):
            scope.register(dependency)
        assert dependency.react in reactive.react._dependencies
