from __future__ import annotations

import functools
from typing import Callable, overload, cast, Generic, Any

from reactives._callable import CallableDefinition, ParamT, ReturnT, CallableReactorController
from reactives.instance import ReactiveInstance, ReactiveInstanceT, InstanceAttributeDefinition
from reactives.reactor import ReactorController

try:
    from typing_extensions import Concatenate, Self, TypeAlias
except ImportError:  # pragma: no cover
    from typing import Concatenate, Self, TypeAlias  # type: ignore  # pragma: no cover

Method: TypeAlias = Callable[
    Concatenate[ReactiveInstanceT, ParamT],
    ReturnT,
]


class MethodReactorController(CallableReactorController):
    def __init__(self, callable_definition: CallableDefinition, instance: ReactiveInstance):
        super().__init__(callable_definition)
        self._instance = instance

    def __repr__(self) -> str:
        return f'<{self.__class__.__module__}.{self.__class__.__qualname__} object at {hex(id(self))} for the method "{self._callable_definition.callable.__name__}" of {self._instance.__class__.__module__}.{self._instance.__class__.__qualname__} at {hex(id(self._instance))}>'

    def _on_trigger(self) -> None:
        if self._callable_definition.on_trigger_call:
            self._callable_definition.callable(self._instance)


class _MethodDefinition(CallableDefinition[Concatenate[ReactiveInstanceT, ParamT], ReturnT], InstanceAttributeDefinition, Generic[ReactiveInstanceT, ParamT, ReturnT]):
    def __init__(
        self,
        function: Method[ReactiveInstanceT, ParamT, ReturnT],
        *args: Any,
        on_trigger_call: bool,
        **kwargs: Any,
    ):
        super().__init__(
            function,  # type: ignore[arg-type]
            function,
            *args,
            on_trigger_call=on_trigger_call,
            **kwargs,
        )

    def create_instance_attribute_reactor_controller(self, instance: ReactiveInstance) -> ReactorController:
        return MethodReactorController(self, instance)

    @overload
    def __get__(self, instance: None, owner: object) -> Self:
        pass

    @overload
    def __get__(self, instance: ReactiveInstanceT, owner: object) -> Callable[ParamT, ReturnT]:
        pass

    def __get__(self, instance: ReactiveInstanceT | None, owner: object) -> Callable[ParamT, ReturnT] | Self:
        if instance is None:
            return self

        def call(*args: ParamT.args, **kwargs: ParamT.kwargs) -> ReturnT:
            return self._call(
                cast(ReactiveInstanceT, instance).react[self],
                instance,  # type: ignore[arg-type]
                *args,
                **kwargs,
            )
        functools.update_wrapper(call, self)
        return call

    def __call__(self, instance: ReactiveInstanceT, *args: ParamT.args, **kwargs: ParamT.kwargs) -> ReturnT:
        return self._call(
            instance.react[self],
            instance,  # type: ignore[arg-type]
            *args,
            **kwargs,
        )


@overload
def reactive_method(
    *,
    on_trigger_call: bool = False,
) -> Callable[
    [
        Method[ReactiveInstanceT, ParamT, ReturnT],
    ],
    Method[ReactiveInstanceT, ParamT, ReturnT],
]:
    pass


@overload
def reactive_method(
    decorated_method: Method[ReactiveInstanceT, ParamT, ReturnT],
    *,
    on_trigger_call: bool = False,
) -> Method[ReactiveInstanceT, ParamT, ReturnT]:
    pass


def reactive_method(  # type: ignore[misc]
    method: Method[ReactiveInstanceT, ParamT, ReturnT] | None = None,
    *,
    on_trigger_call: bool = False,
) -> Method[ReactiveInstanceT, ParamT, ReturnT] | Callable[
    [
        Method[ReactiveInstanceT, ParamT, ReturnT],
    ],
    Method[ReactiveInstanceT, ParamT, ReturnT],
]:
    def _decorator(decorator_method: Method[ReactiveInstanceT, ParamT, ReturnT]) -> Method[ReactiveInstanceT, ParamT, ReturnT]:
        return _MethodDefinition(
            decorator_method,
            on_trigger_call=on_trigger_call,
        )
    return _decorator(method) if method else _decorator
