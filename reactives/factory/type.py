import inspect
from typing import Type

from reactives import ReactorController, Reactive, is_reactive, reactive_factory


class InstanceAttribute:
    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        raise NotImplementedError


class _ReactiveInstanceAttribute:
    def __init__(self, reactor_controller: ReactorController):
        self.react = reactor_controller


class _InstanceReactorController(ReactorController):
    def __init__(self, instance):
        super().__init__()
        self._instance = instance
        self._reactive_attributes = {}

        # Initialize each reactive instance attribute and autowire it. Get the attributes through the class, though, so
        # we can get the actual descriptors.
        for name, attribute in inspect.getmembers(instance.__class__, self._is_reactive_instance_attribute):
            assert isinstance(attribute, InstanceAttribute)
            reactor_controller = attribute.create_instance_attribute_reactor_controller(instance)
            reactive_attribute = _ReactiveInstanceAttribute(reactor_controller)
            reactive_attribute.react(instance)
            self._reactive_attributes[name] = self._reactive_attributes[attribute] = reactive_attribute

    def _is_reactive_instance_attribute(self, attribute) -> bool:
        if is_reactive(attribute):
            return True

        if isinstance(attribute, InstanceAttribute):
            return True

        return False

    def getattr(self, name_or_attribute) -> Reactive:
        """
        Get a reactive instance attribute.
        """
        try:
            return self._reactive_attributes[name_or_attribute]
        except KeyError:
            raise AttributeError('No reactive attribute "%s" exists.' % name_or_attribute)


@reactive_factory(type)
def _reactive_type(decorated_class: Type) -> type:
    # Override the initializer to instantiate an instance-level reactor controller.
    original_init = decorated_class.__init__

    def init(self, *args, **kwargs):
        self.react = _InstanceReactorController(self)
        original_init(self, *args, **kwargs)

    decorated_class.__init__ = init

    return decorated_class
