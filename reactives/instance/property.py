from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Callable, TypeVar, overload, Generic, Any, cast, Iterator

from reactives import scope, Reactive
from reactives.instance import ReactiveInstance, Setattr, Delattr, ReactiveInstanceT
from reactives.reactor import ReactorController

try:
    from typing_extensions import Self
except ImportError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover

T = TypeVar('T')
GetterT = TypeVar('GetterT')
SetterT = TypeVar('SetterT')
Getter = Callable[[ReactiveInstanceT], GetterT]
Setter = Callable[[ReactiveInstanceT, SetterT], None]
Deleter = Callable[[ReactiveInstanceT], None]


class _PropertyReactorController(ReactorController):
    def __init__(self, instance: ReactiveInstance, attribute_name: str):
        super().__init__()
        self._instance = instance
        self._attribute_name = attribute_name

    def __repr__(self) -> str:
        return f'<{self.__class__.__module__}.{self.__class__.__qualname__} object at {hex(id(self))} for the property "{self._attribute_name}" of {self._instance.__class__.__module__}.{self._instance.__class__.__qualname__} at {hex(id(self._instance))}>'

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state['_instance'] = self._instance
        state['_attribute_name'] = self._attribute_name
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        super().__setstate__(state)
        self._instance = state['_instance']
        self._attribute_name = state['_attribute_name']

    def __copy__(self) -> Self:
        copied = super().__copy__()
        copied._instance = self._instance
        copied._attribute_name = self._attribute_name
        copied._dependencies = self._dependencies
        return copied

    def _on_trigger(self) -> None:
        attribute_definition = cast(_PropertyDefinition, self._instance.react.getattr_definition(self._attribute_name))
        if attribute_definition._on_trigger_delete:
            delattr(self._instance, self._attribute_name)


class _PropertyDefinition(Setattr[ReactiveInstanceT, SetterT], Delattr[ReactiveInstanceT], Generic[ReactiveInstanceT, GetterT, SetterT]):
    def __init__(
        self,
        getter: Getter[ReactiveInstanceT, GetterT],
        *,
        on_trigger_delete: bool = False,
    ):
        super().__init__(getter)
        self._getter = getter
        self._on_trigger_delete = on_trigger_delete

    def create_instance_attribute_reactor_controller(self, instance: ReactiveInstanceT) -> ReactorController:
        return _PropertyReactorController(instance, self._getter.__name__)

    def __call__(self, instance: ReactiveInstanceT) -> GetterT:
        reactive_instance_attribute = instance.react[self]
        scope.register(reactive_instance_attribute)
        with scope.collect(reactive_instance_attribute):
            value = self._getter(instance)
            if isinstance(value, Reactive):
                scope.register(value)
            return value

    @contextmanager
    def setattr(self, instance: ReactiveInstanceT, name: str, value: SetterT) -> Iterator[None]:
        reactive_instance_attribute = instance.react[self]
        with scope.collect(reactive_instance_attribute):
            yield
            if isinstance(value, Reactive):
                scope.register(value)
        reactive_instance_attribute.react._trigger()

    @contextmanager
    def delattr(self, instance: ReactiveInstanceT, name: str) -> Iterator[None]:
        reactive_instance_attribute = instance.react[self]
        with scope.collect(reactive_instance_attribute):
            yield
        reactive_instance_attribute.react._trigger()


@overload
def reactive_property(
    *,
    on_trigger_delete: bool = False,
) -> Callable[[Callable[[ReactiveInstanceT], GetterT]], Getter[ReactiveInstanceT, GetterT]]:
    pass


@overload
def reactive_property(
    getter: Getter[ReactiveInstanceT, GetterT],
    *,
    on_trigger_delete: bool = False,
) -> Getter[ReactiveInstanceT, GetterT]:
    pass


def reactive_property(
    getter: Getter[ReactiveInstanceT, GetterT] | None = None,
    *,
    on_trigger_delete: bool = False,
) -> Getter[ReactiveInstanceT, GetterT] | Callable[[Getter[ReactiveInstanceT, GetterT]], Getter[ReactiveInstanceT, GetterT]]:
    def _decorator(
        decorator_getter: Getter[ReactiveInstanceT, GetterT],
    ) -> _PropertyDefinition[ReactiveInstanceT, GetterT, Any]:
        return _PropertyDefinition(
            decorator_getter,
            on_trigger_delete=on_trigger_delete,
        )
    return _decorator(getter) if getter else _decorator
