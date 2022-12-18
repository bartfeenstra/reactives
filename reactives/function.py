from __future__ import annotations

from typing import Callable, Generic, overload, Any

from reactives import Reactive
from reactives._callable import CallableDefinition, CallableReactorController, ParamT, ReturnT
from reactives._decorator import Decorator


class _FunctionDefinition(CallableDefinition[ParamT, ReturnT], Decorator, Reactive, Generic[ParamT, ReturnT]):
    def __init__(self, *args: Any, on_trigger_call: bool, **kwargs: Any):
        super().__init__(*args, on_trigger_call=on_trigger_call, **kwargs)
        self.react = CallableReactorController(
            self.__call__ if on_trigger_call else None,
        )

    def __call__(self, *args: ParamT.args, **kwargs: ParamT.kwargs) -> ReturnT:
        return self._call(self, *args, **kwargs)


@overload
def reactive_function(
    *,
    on_trigger_call: bool = False,
) -> Callable[[Callable[ParamT, ReturnT]], _FunctionDefinition[ParamT, ReturnT]]:
    pass


@overload
def reactive_function(
    decorated_function: Callable[ParamT, ReturnT],
    *,
    on_trigger_call: bool = False,
) -> _FunctionDefinition[ParamT, ReturnT]:
    pass


def reactive_function(  # type: ignore[misc]
    function: Callable[ParamT, ReturnT] | None = None,
    *,
    on_trigger_call: bool = False,
) -> _FunctionDefinition[ParamT, ReturnT] | Callable[[Callable[ParamT, ReturnT]], _FunctionDefinition[ParamT, ReturnT]]:
    def _decorator(decorator_function: Callable[ParamT, ReturnT]) -> _FunctionDefinition[ParamT, ReturnT]:
        return _FunctionDefinition(
            decorator_function,
            on_trigger_call=on_trigger_call,
        )
    return _decorator(function) if function else _decorator
