import functools
from typing import Callable, Sequence, TypeVar, Any

from reactives import scope, is_reactive, assert_reactive, ReactorController
from reactives.reactive import UnsupportedReactive, reactive_type
from reactives.reactive.type import InstanceAttribute, _InstanceReactorController

T = TypeVar('T')


class _ReactivePropertyReactorController(ReactorController):
    def __init__(self, reactive_property: '_ReactiveProperty', instance):
        super().__init__()
        self._reactive_property = reactive_property
        self._instance = instance
        self._dependencies = []

    def trigger(self) -> None:
        for on_trigger in self._reactive_property._on_trigger:
            on_trigger(self._instance)
        super().trigger()


class _ReactiveProperty(InstanceAttribute):
    def __init__(self, decorated_property: property, on_trigger: Sequence[Callable[[T], None]] = ()):
        if not decorated_property.fget:
            raise UnsupportedReactive('Properties must have a getter to be made reactive.')
        self._decorated_property = decorated_property
        self._on_trigger = on_trigger

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _ReactivePropertyReactorController(self, instance)

    def __get__(self, instance, owner=None) -> Any:
        if instance is None:
            return self
        return self.__get__from_instance(instance, owner)

    def __get__from_instance(self, instance, owner=None):
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
        return _ReactiveProperty(self._decorated_property.setter(*args, **kwargs))

    def deleter(self, *args, **kwargs):
        return _ReactiveProperty(self._decorated_property.deleter(*args, **kwargs))


@reactive_type.register(property)
def reactive_property(decorated_property, on_trigger: Sequence[Callable[[T], None]] = ()):
    _reactive_property = _ReactiveProperty(decorated_property, on_trigger)
    functools.update_wrapper(_reactive_property, decorated_property)
    return _reactive_property
