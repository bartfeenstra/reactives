import copy
import functools
import inspect
from contextlib import suppress
from typing import Dict, Any, Type
from warnings import warn

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self  # type: ignore

from reactives.factory import reactive_factory, Reactive
from reactives.reactor import ReactorController


class InstanceAttribute:
    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        raise NotImplementedError


class _ReactiveInstanceAttribute(Reactive):
    def __init__(self, reactor_controller: ReactorController):
        self.react = reactor_controller


class _InstanceReactorController(ReactorController):
    def __init__(self, instance):
        super().__init__()
        self._instance = instance
        self._reactive_attributes: Dict[Any, _ReactiveInstanceAttribute] = {}
        self._initialized = False

    def copy_for_instance(self, instance: Any):
        copied = copy.copy(self)
        copied._instance = instance
        self._rewire_to_copy(copied)
        return copied

    def _rewire_to_copy(self, copied: '_InstanceReactorController') -> None:
        for reactive_attr_name, reactive_attribute in copied._reactive_attributes.items():
            with suppress(ValueError):
                copied._reactive_attributes[reactive_attr_name].react.shutdown(self._instance)
            copied._reactive_attributes[reactive_attr_name].react(copied._instance)

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
        self._reactive_attributes = {}
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

        for reactive_attr_name, reactive_attr_value in inspect.getmembers(self._instance.__class__, lambda x: isinstance(x, InstanceAttribute)):
            self._initialize_reactive_attribute(reactive_attr_name, reactive_attr_value)

    def _initialize_reactive_attribute(self, reactive_attr_name: str, reactive_attr_value: Any) -> None:
        if reactive_attr_name in self._reactive_attributes:
            # When pickling or copying, reactive attributes with non-string keys are omitted. We must recover those
            # here.
            self._reactive_attributes[reactive_attr_value] = self._reactive_attributes[reactive_attr_name]
            return

        reactor_controller = reactive_attr_value.create_instance_attribute_reactor_controller(self._instance)
        reactive_attribute = _ReactiveInstanceAttribute(reactor_controller)
        reactive_attribute.react(self._instance)
        # Store reactive attributes by name as well as their original value, as we need access through both.
        self._reactive_attributes[reactive_attr_name] = self._reactive_attributes[reactive_attr_value] = reactive_attribute

    def getattr(self, name_or_attribute: Any) -> Reactive:
        """
        Get a reactive instance attribute.
        """
        self._initialize_reactive_instance_attributes()
        try:
            return self._reactive_attributes[name_or_attribute]
        except KeyError:
            raise AttributeError(f'No reactive attribute "{name_or_attribute}" exists.')

    def __getitem__(self, name_or_attribute: Any) -> Reactive:
        return self.getattr(name_or_attribute)


class ReactiveInstance(Reactive):
    """
    Define a reactive instance.

    Although this does not extend reactives.factory.Reactive, it will pass isinstance(x, reactives.factory.Reactive)
    checks.
    """

    react: _InstanceReactorController


@reactive_factory(type)
def _reactive_type(decorated_class: Type[ReactiveInstance]) -> Type[ReactiveInstance]:
    if not issubclass(decorated_class, ReactiveInstance):
        warn(f'{decorated_class} was made reactive. For accurate type hinting it must also extend `{ReactiveInstance}`.', stacklevel=2)

    # Override the initializer to instantiate an instance-level reactor controller.
    original_init = decorated_class.__init__

    @functools.wraps(original_init)
    def _init(self, *args, **kwargs):
        self.react = _InstanceReactorController(self)
        original_init(self, *args, **kwargs)
    setattr(decorated_class, '__init__', _init)

    original_copy = getattr(decorated_class, '__copy__', None)

    def _copy(self):
        if original_copy is not None:
            copied = original_copy(self)
        else:
            copied = self.__class__.__new__(self.__class__)

        copied.react = self.react.copy_for_instance(copied)

        return copied
    if original_copy is not None:
        functools.update_wrapper(_copy, original_copy)
    setattr(decorated_class, '__copy__', _copy)

    return decorated_class
