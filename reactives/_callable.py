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
    def __init__(self, on_trigger_call: Callable[[], Any] | None = None):
        super().__init__()
        self._on_trigger_call = on_trigger_call

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state['_on_trigger_call'] = self._on_trigger_call
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        super().__setstate__(state)
        self._on_trigger_call = state['_on_trigger_call']

    def __copy__(self) -> Self:
        copied = super().__copy__()
        copied._on_trigger_call = self._on_trigger_call
        copied._dependencies = self._dependencies
        return copied

    def _on_trigger(self) -> None:
        if self._on_trigger_call is not None:
            self._on_trigger_call()


class CallableDefinition(Generic[ParamT, ReturnT]):
    def __init__(self, function: Callable[ParamT, ReturnT], *args: Any, on_trigger_call: bool, **kwargs: Any):
        functools.update_wrapper(self, function)
        super().__init__(*args, **kwargs)
        self._decorated_function = function
        self._on_trigger_call = on_trigger_call

    def _call(self, reactive_attribute: Reactive, *args: ParamT.args, **kwargs: ParamT.kwargs) -> ReturnT:
        scope.register(reactive_attribute)
        with scope.collect(reactive_attribute):
            return self._decorated_function(*args, **kwargs)
