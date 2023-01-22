from __future__ import annotations

import functools
from typing import Callable, Dict, Any, TypeVar, Generic

from reactives import scope, Reactive
from reactives.reactor import ReactorController

try:
    from typing_extensions import ParamSpec, Self
except ImportError:  # pragma: no cover
    from typing import ParamSpec, Self  # type: ignore  # pragma: no cover

ParamT = ParamSpec('ParamT')
ReturnT = TypeVar('ReturnT', covariant=True)


class CallableReactorController(ReactorController):
    def __init__(self, callable_definition: CallableDefinition):
        super().__init__()
        self._callable_definition = callable_definition

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state['_callable_definition'] = self._callable_definition
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        super().__setstate__(state)
        self._callable_definition = state['_callable_definition']

    def __copy__(self) -> Self:
        copied = super().__copy__()
        copied._callable_definition = self._callable_definition
        copied._dependencies = self._dependencies
        return copied

    def _on_trigger(self) -> None:
        if self._callable_definition.on_trigger_call:
            self._callable_definition.callable()


class CallableDefinition(Generic[ParamT, ReturnT]):
    def __init__(self, _callable: Callable[ParamT, ReturnT], *args: Any, on_trigger_call: bool = False, **kwargs: Any):
        functools.update_wrapper(self, _callable)
        super().__init__(*args, **kwargs)
        self.callable = _callable
        self.on_trigger_call = on_trigger_call

    def _call(self, reactive_attribute: Reactive, *args: ParamT.args, **kwargs: ParamT.kwargs) -> ReturnT:
        scope.register(reactive_attribute)
        with scope.collect(reactive_attribute):
            return self.callable(*args, **kwargs)
