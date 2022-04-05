from __future__ import annotations

import functools
from typing import Callable, Optional, Dict, Any, cast

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self  # type: ignore


from reactives import scope
from reactives.factory import reactive_factory, Reactive
from reactives.factory.type import InstanceAttribute, ReactiveInstance
from reactives.reactor import ReactorController


class _FunctionReactorController(ReactorController):
    def __init__(self, on_trigger_call: Optional[Callable] = None):
        super().__init__()
        self._on_trigger_call = on_trigger_call

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state['_on_trigger_call'] = self._on_trigger_call
        state['_dependencies'] = self._dependencies
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        super().__setstate__(state)
        self._on_trigger_call = state['_on_trigger_call']
        self._dependencies = state['_dependencies']

    def __copy__(self) -> Self:
        copied = super().__copy__()
        copied._on_trigger_call = self._on_trigger_call
        copied._dependencies = self._dependencies
        return copied

    def trigger(self) -> None:
        if self._on_trigger_call is not None:
            self._on_trigger_call()
        super().trigger()


class _InstanceAttributeOnTrigger:
    def __init__(self, reactive_method: _ReactiveFunction, instance):
        self._reactive_method = reactive_method
        self._instance = instance

    def __call__(self):
        self._reactive_method._call(self._instance.react[self._reactive_method], self._instance)


class _ReactiveFunction(InstanceAttribute, Reactive):
    def __init__(self, decorated_function: Callable, on_trigger_call: bool):
        self._decorated_function = decorated_function
        self._on_trigger_call = on_trigger_call
        self.react = _FunctionReactorController(
            self.__call__ if on_trigger_call else None,
        )

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _FunctionReactorController(
            _InstanceAttributeOnTrigger(self, instance) if self._on_trigger_call else None,
        )

    def __get__(self, instance: Optional[ReactiveInstance], owner):
        if instance is None:
            return self

        def call(*args, **kwargs):
            reactive_instance_attribute = cast(ReactiveInstance, instance).react[self]
            with scope.collect(reactive_instance_attribute):
                return self._decorated_function(instance, *args, **kwargs)
        functools.update_wrapper(call, self)

        return call

    def __call__(self, *args, **kwargs):
        return self._call(self, *args, **kwargs)

    def _call(self, reactive_function: Reactive, *args, **kwargs):
        with scope.collect(reactive_function):
            return self._decorated_function(*args, **kwargs)


@reactive_factory(type(lambda: ()))
def _reactive_function(decorated_function: Callable, on_trigger_call: bool = False) -> Reactive:
    reactive_function = _ReactiveFunction(decorated_function, on_trigger_call)
    functools.update_wrapper(reactive_function, decorated_function)
    return reactive_function
