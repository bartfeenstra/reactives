import functools
from typing import Optional

from reactives import scope, ReactorController, assert_reactive, Reactive
from reactives.reactive import reactive_type
from reactives.reactive.type import InstanceAttribute
from reactives.typing import function


class _FunctionReactorController(ReactorController):
    def __init__(self, on_trigger_call: Optional[callable]):
        super().__init__()
        self._on_trigger_call = on_trigger_call
        self._dependencies = []

    def trigger(self) -> None:
        if self._on_trigger_call is not None:
            self._on_trigger_call()
        super().trigger()


class _ReactiveFunction(InstanceAttribute):
    def __init__(self, decorated_function: callable, on_trigger_call: bool):
        self._decorated_function = decorated_function
        self._on_trigger_call = on_trigger_call
        self.react = _FunctionReactorController(
            self.__call__ if on_trigger_call else None,
        )

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _FunctionReactorController(
            lambda *args, **kwargs: self._call(instance.react.getattr(
                self), instance, *args, **kwargs) if self._on_trigger_call else None,
        )

    def __get__(self, instance, owner):
        if instance is None:
            return self

        def call(*args, **kwargs):
            assert_reactive(instance)
            reactive_instance_attribute = instance.react.getattr(self)
            with scope.collect(reactive_instance_attribute, reactive_instance_attribute.react._dependencies):
                return self._decorated_function(instance, *args, **kwargs)

        return call

    def __call__(self, *args, **kwargs):
        return self._call(self, *args, **kwargs)

    def _call(self, reactive_function: Reactive, *args, **kwargs):
        with scope.collect(reactive_function, reactive_function.react._dependencies):
            return self._decorated_function(*args, **kwargs)


@reactive_type.register(function)
def reactive_function(decorated_function, on_trigger_call: bool = False):
    _reactive_function = _ReactiveFunction(decorated_function, on_trigger_call)
    functools.update_wrapper(_reactive_function, decorated_function)
    return _reactive_function
