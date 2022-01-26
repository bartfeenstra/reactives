from unittest import TestCase

from reactives.reactive import reactive
from reactives.reactive.type import _InstanceReactorController
from reactives.tests import assert_reactor_called, assert_not_reactor_called, assert_is_reactive


class InstanceReactorControllerTest(TestCase):
    def test_getattr_with_reactive_attribute(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        assert_is_reactive(sut.getattr('subject'))

    def test_getattr_with_non_existent_reactive_attribute(self) -> None:
        @reactive
        class Subject:
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        with self.assertRaises(AttributeError):
            sut.getattr('subject')


class ReactiveTypeTest(TestCase):
    def test_instance_trigger_without_reactors(self) -> None:
        @reactive
        class Subject:
            pass
        Subject().react.trigger()

    def test_instance_trigger_with_instance_reactor(self) -> None:
        @reactive
        class Subject:
            pass
        subject = Subject()
        with assert_reactor_called(subject):
            subject.react.trigger()

    def test_instance_trigger_with_instance_attribute_reactor(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with assert_not_reactor_called(subject.react.getattr('subject')):
            Subject().react.trigger()

    def test_instance_attribute_trigger_without_reactors(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        Subject().react.getattr('subject').react.trigger()

    def test_instance_attribute_trigger_with_instance_reactor(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with assert_reactor_called(subject):
            subject.react.getattr('subject').react.trigger()

    def test_instance_attribute_trigger_with_instance_attribute_reactor(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with assert_reactor_called(subject.react.getattr('subject')):
            subject.react.getattr('subject').react.trigger()
