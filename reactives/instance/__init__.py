from __future__ import annotations

import copy
import functools
import inspect
from collections import defaultdict
from contextlib import suppress
from typing import Dict, Any, TypeVar, Generic, MutableMapping, Iterator, MutableSequence, ContextManager, Type, \
    ClassVar

from reactives import Reactive
from reactives._decorator import Decorator
from reactives.reactor import ReactorController, ReactorControllerT

try:
    from typing_extensions import Self
except ImportError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover


T = TypeVar('T')


class _ReactiveInstanceAttribute(Reactive):
    def __init__(self, reactor_controller: ReactorControllerT):
        super().__init__()
        self.react = reactor_controller


class ReactiveInstance(Reactive):
    react: _ReactiveInstanceReactorController

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.react = _ReactiveInstanceReactorController(self)

    def __copy__(self) -> Self:
        copied = type(self)()
        copied.react._update(self.react)
        return copied

    def __setattr__(self, name: str, value: Any) -> None:
        attribute_definition = None
        with suppress(AttributeError):
            attribute_definition = self.react.getattr_definition(name)
        if attribute_definition and isinstance(attribute_definition, Setattr):
            with attribute_definition.setattr(self, name, value):
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        attribute_definition = None
        with suppress(AttributeError):
            attribute_definition = self.react.getattr_definition(name)
        if attribute_definition and isinstance(attribute_definition, Delattr):
            with attribute_definition.delattr(self, name):
                super().__delattr__(name)
        else:
            super().__delattr__(name)


ReactiveInstanceT = TypeVar('ReactiveInstanceT', bound=ReactiveInstance)


class InstanceAttributeDefinition(Generic[ReactiveInstanceT], Decorator):
    _registry: ClassVar[MutableMapping[str, MutableSequence[InstanceAttributeDefinition]]] = defaultdict(list)

    def __init__(self, target: object, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        functools.update_wrapper(
            self,
            target,  # type: ignore[arg-type]
        )
        InstanceAttributeDefinition.register(self)

    def __repr__(self) -> str:
        return f'<{self.__class__.__module__}.{self.__class__.__qualname__} for {self.__module__}.{self.__qualname__}>'

    @classmethod
    def _assert_not_local(cls, name: str) -> None:
        """
        Assert that an attribute is not of a local class.

        Local classes cannot be accessed from outside their scope, and can potentially be redefined, so are unsuitable
        for registration by name.
        """
        if '<locals>' in name:
            raise ValueError(f'Attributes of local classes cannot be made reactive. Move the class {name[0:name.rfind(".")]} outside the function {name[0:name.find("<locals>") - 1]}().')

    @classmethod
    def register(cls, attribute_definition: InstanceAttributeDefinition) -> None:
        name = '.'.join((attribute_definition.__module__, attribute_definition.__qualname__))
        InstanceAttributeDefinition._assert_not_local(name)
        InstanceAttributeDefinition._registry[name].append(attribute_definition)

    @classmethod
    def iter(cls, reactive_type: Type[ReactiveInstance], attribute_name: str) -> Iterator[InstanceAttributeDefinition]:
        for mro_type in reactive_type.__mro__:
            name = '.'.join((mro_type.__module__, mro_type.__qualname__, attribute_name))
            InstanceAttributeDefinition._assert_not_local(name)
            for registered_name in InstanceAttributeDefinition._registry:
                if registered_name == name or registered_name.startswith(f'{name}.'):
                    yield from InstanceAttributeDefinition._registry[registered_name]

    def create_instance_attribute_reactor_controller(self, instance: ReactiveInstanceT) -> ReactorController:
        raise NotImplementedError


class Setattr(InstanceAttributeDefinition[ReactiveInstanceT], Generic[ReactiveInstanceT, T]):
    def setattr(self, instance: ReactiveInstanceT, name: str, value: T) -> ContextManager[None]:
        raise NotImplementedError


class Delattr(InstanceAttributeDefinition[ReactiveInstanceT], Generic[ReactiveInstanceT]):
    def delattr(self, instance: ReactiveInstanceT, name: str) -> ContextManager[None]:
        raise NotImplementedError


class _ReactiveInstanceReactorController(ReactorController, Generic[ReactiveInstanceT]):
    def __init__(self, instance: ReactiveInstanceT):
        super().__init__()
        self._instance = instance
        self._reactive_attributes: Dict[str | InstanceAttributeDefinition, _ReactiveInstanceAttribute] = {}
        self._initialized = False

    def __repr__(self) -> str:
        return f'<{self.__class__.__module__}.{self.__class__.__qualname__} object at {hex(id(self))} for {self._instance.__class__.__module__}.{self._instance.__class__.__qualname__} at {hex(id(self._instance))}>'

    def _update(self, other: Self) -> None:
        for attribute_name, _ in other._reactive_attributes.items():
            with suppress(ValueError):
                self[attribute_name].react.shutdown(other._instance)
            self[attribute_name].react(self._instance)

    def __getstate__(self) -> Dict[str, Any]:
        state = super().__getstate__()
        state['_instance'] = self._instance
        state['_reactive_attributes'] = {
            reactive_attr_name: reactive_attribute
            for reactive_attr_name, reactive_attribute in self._reactive_attributes.items()
            # Filter out reactive attributes set by value, and keep those set by attribute name. The value keys will be
            # restored upon unpickling.
            if isinstance(reactive_attr_name, str)
        }
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        super().__setstate__(state)
        self._instance = state['_instance']
        self._reactive_attributes = state['_reactive_attributes']
        self._initialized = False

    def __copy__(self) -> Self:
        self._initialize_reactive_instance_attributes()
        copied = super().__copy__()
        copied._instance = self._instance
        copied._reactive_attributes = copy.copy(self._reactive_attributes)
        copied._initialized = True
        return copied

    def _initialize_reactive_instance_attributes(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        for attribute_name, attribute_value in inspect.getmembers(self._instance.__class__):
            for attribute_definition in InstanceAttributeDefinition.iter(
                self._instance.__class__,
                attribute_name,
            ):
                self._initialize_reactive_attribute(
                    attribute_name,
                    attribute_definition,
                )

    def _initialize_reactive_attribute(self, attribute_name: str, attribute_definition: InstanceAttributeDefinition) -> None:
        if attribute_name in self._reactive_attributes:
            # When pickling or copying, reactive attributes with non-string keys are omitted. We must recover those
            # here.
            self._reactive_attributes[attribute_definition] = self._reactive_attributes[attribute_name]
            return

        reactive_attribute_reactor_controller = attribute_definition.create_instance_attribute_reactor_controller(self._instance)
        reactive_attribute = _ReactiveInstanceAttribute(reactive_attribute_reactor_controller)
        reactive_attribute.react(self._instance)
        # Store reactive attributes by name as well as their original value, as we need access through both.
        self._reactive_attributes[attribute_name] = self._reactive_attributes[attribute_definition] = reactive_attribute

    def getattr_reactive(self, name_or_attribute_definition: str | InstanceAttributeDefinition) -> Reactive:
        """
        Get a reactive instance attribute.
        """
        self._initialize_reactive_instance_attributes()
        try:
            return self._reactive_attributes[name_or_attribute_definition]
        except KeyError:
            raise AttributeError(f'No reactive attribute "{name_or_attribute_definition}" exists.')

    def getattr_definition(self, name: str) -> InstanceAttributeDefinition:
        """
        Get the definition for a reactive instance attribute.
        """
        try:
            return next(InstanceAttributeDefinition.iter(
                self._instance.__class__,
                name,
            ))
        except StopIteration:
            raise AttributeError(f'No reactive attribute "{name}" exists.')

    def __getitem__(self, name_or_attribute_definition: str | InstanceAttributeDefinition) -> Reactive:
        return self.getattr_reactive(name_or_attribute_definition)
