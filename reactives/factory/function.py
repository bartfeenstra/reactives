import functools
from typing import Callable, Optional, Dict, Any

from reactives import scope, ReactorController, assert_reactive, Reactive, reactive_factory
from reactives.factory.type import InstanceAttribute
from reactives.typing import function


class _FunctionReactorController(ReactorController):
    def __init__(self, on_trigger_call: Optional[callable]):
        super().__init__()
        self._on_trigger_call = on_trigger_call
        self._dependencies = []

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state['_on_trigger_call'] = self._on_trigger_call
        state['_dependencies'] = self._dependencies
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        super().__setstate__(state)
        self._on_trigger_call = state['_on_trigger_call']
        self._dependencies = state['_dependencies']

    def trigger(self) -> None:
        if self._on_trigger_call is not None:
            self._on_trigger_call()
        super().trigger()


class _InstanceAttributeOnTrigger:
    def __init__(self, reactive_method: '_ReactiveFunction', instance):
        self._reactive_method = reactive_method
        self._instance = instance

    def __call__(self):
        self._reactive_method._call(self._instance.react.getattr(self._reactive_method), self._instance)


class _ReactiveFunction(InstanceAttribute):
    def __init__(self, decorated_function: callable, on_trigger_call: bool):
        self._decorated_function = decorated_function
        self._on_trigger_call = on_trigger_call
        self.react = _FunctionReactorController(
            self.__call__ if on_trigger_call else None,
        )

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _FunctionReactorController(
            _InstanceAttributeOnTrigger(self, instance) if self._on_trigger_call else None,
        )

    def __get__(self, instance, owner):
        if instance is None:
            return self

        def call(*args, **kwargs):
            assert_reactive(instance)
            reactive_instance_attribute = instance.react.getattr(self)
            with scope.collect(reactive_instance_attribute, reactive_instance_attribute.react._dependencies):
                return self._decorated_function(instance, *args, **kwargs)
        functools.update_wrapper(call, self)

        return call

    def __call__(self, *args, **kwargs):
        return self._call(self, *args, **kwargs)

    def _call(self, reactive_function: Reactive, *args, **kwargs):
        with scope.collect(reactive_function, reactive_function.react._dependencies):
            return self._decorated_function(*args, **kwargs)


@reactive_factory(function)
def _reactive_function(decorated_function: function, on_trigger_call: bool = False) -> Callable:
    reactive_function = _ReactiveFunction(decorated_function, on_trigger_call)
    functools.update_wrapper(reactive_function, decorated_function)
    return reactive_function
