from __future__ import annotations

from typing import Callable, Generic, overload, Any

from reactives import Reactive
from reactives._callable import CallableDefinition, CallableReactorController, ParamT, ReturnT
from reactives._decorator import Decorator


class FunctionReactorController(CallableReactorController):
    def __repr__(self) -> str:
        return f'<{self.__class__.__module__}.{self.__class__.__qualname__} object at {hex(id(self))} for the function {self._callable_definition.callable.__module__}.{self._callable_definition.callable.__qualname__} at {hex(id(self._callable_definition.callable))}>'


class _FunctionDefinition(CallableDefinition[ParamT, ReturnT], Decorator, Reactive, Generic[ParamT, ReturnT]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.react = FunctionReactorController(self)

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
