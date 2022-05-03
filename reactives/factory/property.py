import functools
from typing import Any, Dict, Callable, Optional, TypeVar

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self  # type: ignore

from reactives import scope
from reactives.factory import reactive_factory, UnsupportedReactive, Reactive, reactive
from reactives.factory.type import InstanceAttribute, ReactiveInstance
from reactives.reactor import ReactorController

T = TypeVar('T')


class _PropertyReactorController(ReactorController):
    def __init__(self, instance: T, deleter: Optional[Callable[[T], None]] = None):
        super().__init__()
        self._instance = instance
        self._deleter = deleter

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state['_instance'] = self._instance
        state['_deleter'] = self._deleter
        state['_dependencies'] = self._dependencies
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        super().__setstate__(state)
        self._instance = state['_instance']
        self._deleter = state['_deleter']
        self._dependencies = state['_dependencies']

    def __copy__(self) -> Self:
        copied = super().__copy__()
        copied._instance = self._instance
        copied._deleter = self._deleter
        copied._dependencies = self._dependencies
        return copied

    def trigger(self, on_trigger_delete: bool = True) -> None:
        if self._deleter and on_trigger_delete:
            self._deleter(self._instance)
        super().trigger()


class _ReactiveProperty(property, InstanceAttribute):
    def __init__(self, decorated_property: property, on_trigger_delete: bool, auto_collect_scope: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not decorated_property.fget:
            raise UnsupportedReactive('Properties must have a getter to be made reactive.')
        self._decorated_property = decorated_property
        self._on_trigger_delete = on_trigger_delete
        self._auto_collect_scope = auto_collect_scope

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _PropertyReactorController(
            instance,
            self._decorated_property.fdel if self._on_trigger_delete else None,
        )

    def __get__(self, instance: Optional[ReactiveInstance], owner=None) -> Any:
        if instance is None:
            return self
        return self._get__from_instance(instance, owner)

    def _get__from_instance(self, instance: ReactiveInstance, owner=None) -> Any:
        if not isinstance(instance, ReactiveInstance):
            raise ValueError(f'Cannot access a reactive property on {instance}. Did you forget to decorate {type(instance)} with @{reactive.__name__}?')
        if self._auto_collect_scope:
            with scope.collect(instance.react[self]):
                value = self._decorated_property.__get__(instance, owner)
                if isinstance(value, Reactive):
                    scope.register(value)
                return value
        return self._decorated_property.__get__(instance, owner)

    def __set__(self, instance, value) -> None:
        reactive_instance_attribute = instance.react[self]
        scope.clear(reactive_instance_attribute)
        self._decorated_property.__set__(instance, value)
        if isinstance(value, Reactive):
            reactive_instance_attribute.react._dependencies.append(value)
            value.react.react_weakref(reactive_instance_attribute)
        reactive_instance_attribute.react.trigger(on_trigger_delete=False)

    def __delete__(self, instance) -> None:
        reactive_instance_attribute = instance.react[self]
        scope.clear(reactive_instance_attribute)
        self._decorated_property.__delete__(instance)
        instance.react[self].react.trigger()

    def setter(self, *args, **kwargs):
        return _ReactiveProperty(self._decorated_property.setter(*args, **kwargs), self._on_trigger_delete, self._auto_collect_scope)

    def deleter(self, *args, **kwargs):
        return _ReactiveProperty(self._decorated_property.deleter(*args, **kwargs), self._on_trigger_delete, self._auto_collect_scope)


@reactive_factory(property)
def _reactive_property(decorated_property: property, on_trigger_delete: bool = True, auto_collect_scope: bool = True) -> _ReactiveProperty:
    reactive_property = _ReactiveProperty(decorated_property, on_trigger_delete, auto_collect_scope)
    # property is not technically a callable, but calling functools.update_wrapper() on it works, so ignore type errors.
    functools.update_wrapper(reactive_property, decorated_property)  # type: ignore
    return reactive_property
