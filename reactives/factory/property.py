import functools
from typing import Any, Dict, Callable, Optional, TypeVar

from reactives import scope, is_reactive, assert_reactive, ReactorController, reactive_factory, UnsupportedReactive
from reactives.factory.type import InstanceAttribute, _InstanceReactorController


T = TypeVar('T')


class _PropertyReactorController(ReactorController):
    def __init__(self, instance: T, deleter: Optional[Callable[[T], None]] = None):
        super().__init__()
        self._instance = instance
        self._deleter = deleter
        self._dependencies = []

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

    def __copy__(self):
        copied = super().__copy__()
        copied._instance = self._instance
        copied._deleter = self._deleter
        copied._dependencies = self._dependencies
        return copied

    def trigger(self) -> None:
        if self._deleter:
            self._deleter(self._instance)
        super().trigger()


class _ReactiveProperty(InstanceAttribute):
    def __init__(self, decorated_property: property, on_trigger_delete: bool):
        if not decorated_property.fget:
            raise UnsupportedReactive('Properties must have a getter to be made reactive.')
        self._decorated_property = decorated_property
        self._on_trigger_delete = on_trigger_delete

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _PropertyReactorController(
            instance,
            self._decorated_property.fdel if self._on_trigger_delete else None,
        )

    def __get__(self, instance, owner=None) -> Any:
        if instance is None:
            return self
        return self._get__from_instance(instance, owner)

    def _get__from_instance(self, instance, owner=None):
        assert_reactive(instance, _InstanceReactorController)
        reactive_instance_attribute = instance.react.getattr(self)
        with scope.collect(reactive_instance_attribute, reactive_instance_attribute.react._dependencies):
            return self._decorated_property.__get__(instance, owner)

    def __set__(self, instance, value) -> None:
        reactive_instance_attribute = instance.react.getattr(self)
        scope.clear(reactive_instance_attribute, reactive_instance_attribute.react._dependencies)
        self._decorated_property.__set__(instance, value)
        if is_reactive(value):
            reactive_instance_attribute.react._dependencies.append(value)
            value.react.react_weakref(reactive_instance_attribute)
        reactive_instance_attribute.react.trigger()

    def __delete__(self, instance) -> None:
        reactive_instance_attribute = instance.react.getattr(self)
        scope.clear(reactive_instance_attribute, reactive_instance_attribute.react._dependencies)
        self._decorated_property.__delete__(instance)
        instance.react.getattr(self).react.trigger()

    def setter(self, *args, **kwargs):
        return _ReactiveProperty(self._decorated_property.setter(*args, **kwargs), self._on_trigger_delete)

    def deleter(self, *args, **kwargs):
        return _ReactiveProperty(self._decorated_property.deleter(*args, **kwargs), self._on_trigger_delete)


@reactive_factory(property)
def _reactive_property(decorated_property: property, on_trigger_delete: bool = True):
    reactive_property = _ReactiveProperty(decorated_property, on_trigger_delete)
    functools.update_wrapper(reactive_property, decorated_property)
    return reactive_property
