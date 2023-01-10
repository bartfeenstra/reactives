from __future__ import annotations

from contextlib import suppress, contextmanager
from enum import IntEnum, auto
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


class OnTriggerDelete(IntEnum):
    # Do not attempt to delete the property when it is triggered.
    NO_DELETE = auto()
    # Attempt to delete the property when it is triggered, but suppress AttributeError which is raised if the property
    # is non-deletable. If your property deleter may also raise AttributeError for other reasons, use DELETE instead.
    DELETE_IF_DELETABLE = auto()
    # Delete the property when it is triggered.
    DELETE = auto()


class _PropertyReactorController(ReactorController):
    def __init__(self, instance: ReactiveInstance, attribute_name: str):
        super().__init__()
        self._instance = instance
        self._attribute_name = attribute_name

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
        if OnTriggerDelete.DELETE == attribute_definition._on_trigger_delete:
            delattr(self._instance, self._attribute_name)
        elif OnTriggerDelete.DELETE_IF_DELETABLE == attribute_definition._on_trigger_delete:
            with suppress(AttributeError):
                delattr(self._instance, self._attribute_name)


class _PropertyDefinition(Setattr[ReactiveInstanceT, SetterT], Delattr[ReactiveInstanceT], Generic[ReactiveInstanceT, GetterT, SetterT]):
    def __init__(
        self,
        getter: Getter[ReactiveInstanceT, GetterT],
        *,
        on_trigger_delete: OnTriggerDelete = OnTriggerDelete.DELETE_IF_DELETABLE,
    ):
        super().__init__(getter)
        self._getter = getter
        self._on_trigger_delete = on_trigger_delete

    def create_instance_attribute_reactor_controller(self, instance: ReactiveInstanceT) -> ReactorController:
        return _PropertyReactorController(instance, self._getter.__name__)

    def __call__(self, instance: ReactiveInstanceT) -> GetterT:
        scope.register(instance.react[self])
        with scope.collect(instance.react[self]):
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
    on_trigger_delete: OnTriggerDelete = OnTriggerDelete.DELETE_IF_DELETABLE,
) -> Callable[[Callable[[ReactiveInstanceT], GetterT]], Getter[ReactiveInstanceT, GetterT]]:
    pass


@overload
def reactive_property(
    getter: Getter[ReactiveInstanceT, GetterT],
    *,
    on_trigger_delete: OnTriggerDelete = OnTriggerDelete.DELETE_IF_DELETABLE,
) -> Getter[ReactiveInstanceT, GetterT]:
    pass


def reactive_property(
    getter: Getter[ReactiveInstanceT, GetterT] | None = None,
    *,
    on_trigger_delete: OnTriggerDelete = OnTriggerDelete.DELETE_IF_DELETABLE,
) -> Getter[ReactiveInstanceT, GetterT] | Callable[[Getter[ReactiveInstanceT, GetterT]], Getter[ReactiveInstanceT, GetterT]]:
    def _decorator(
        decorator_getter: Getter[ReactiveInstanceT, GetterT],
    ) -> _PropertyDefinition[ReactiveInstanceT, GetterT, Any]:
        return _PropertyDefinition(
            decorator_getter,
            on_trigger_delete=on_trigger_delete,
        )
    return _decorator(getter) if getter else _decorator
