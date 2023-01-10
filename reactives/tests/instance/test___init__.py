from __future__ import annotations

import copy
import pickle

import pytest

from reactives import Reactive
from reactives.instance import ReactiveInstance, _ReactiveInstanceReactorController, InstanceAttributeDefinition
from reactives.instance.method import reactive_method
from reactives.tests import assert_reactor_called, assert_not_reactor_called

try:
    from typing_extensions import Self
except ImportError:
    from typing import Self  # type: ignore


class Subject(ReactiveInstance):
    @reactive_method
    def subject_method(self) -> None:
        pass

    @property
    @reactive_method
    def subject_property(self) -> None:
        return


class SubjectWithCopy(Subject):
    def __copy__(self) -> Self:
        return self.__class__()


class SubjectWithNonReactiveAttribute(ReactiveInstance):
    def subject(self) -> None:
        pass


class SubjectWithoutAttributes(ReactiveInstance):
    pass


class TestReactiveInstanceReactorController:
    def test___copy__(self) -> None:
        sut = _ReactiveInstanceReactorController(Subject())
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    def test_getattr_with_reactive_attribute(self) -> None:
        sut = _ReactiveInstanceReactorController(Subject())
        assert isinstance(sut.getattr_reactive('subject_method'), Reactive)

    def test_getattr_with_existent_non_reactive_attribute(self) -> None:
        sut = _ReactiveInstanceReactorController(SubjectWithNonReactiveAttribute())
        with pytest.raises(AttributeError):
            sut.getattr_reactive('subject_method')

    def test_getattr_with_non_existent_attribute(self) -> None:
        sut = _ReactiveInstanceReactorController(SubjectWithoutAttributes())
        with pytest.raises(AttributeError):
            sut.getattr_reactive('subject_method')

    def test___getitem___with_reactive_attribute(self) -> None:
        sut = _ReactiveInstanceReactorController(Subject())
        assert isinstance(sut['subject_method'], Reactive)

    def test___getitem___with_existent_non_reactive_attribute(self) -> None:
        sut = _ReactiveInstanceReactorController(SubjectWithoutAttributes())
        with pytest.raises(AttributeError):
            sut['subject']

    def test___getitem___with_non_existent_attribute(self) -> None:
        sut = _ReactiveInstanceReactorController(SubjectWithoutAttributes())
        with pytest.raises(AttributeError):
            sut['subject']


class TestReactiveInstance:
    def test_pickle(self) -> None:
        subject = Subject()
        unpickled_subject = pickle.loads(pickle.dumps(subject))
        with assert_not_reactor_called(subject):
            with assert_reactor_called(unpickled_subject):
                unpickled_subject.react.trigger()

    def test___copy___without___copy__(self) -> None:
        subject = Subject()
        copied_subject = copy.copy(subject)
        with assert_not_reactor_called(subject):
            with assert_reactor_called(copied_subject):
                copied_subject.react.trigger()

    def test___copy___with___copy__(self) -> None:
        subject = SubjectWithCopy()
        copied_subject = copy.copy(subject)
        with assert_not_reactor_called(subject):
            with assert_reactor_called(copied_subject):
                copied_subject.react.trigger()

    def test_instance_trigger_without_reactors(self) -> None:
        Subject().react.trigger()

    def test_instance_trigger_with_instance_reactor(self) -> None:
        subject = Subject()
        with assert_reactor_called(subject):
            subject.react.trigger()

    def test_instance_trigger_with_instance_attribute_reactor(self) -> None:
        subject = Subject()
        with assert_not_reactor_called(subject.react['subject_method']):
            Subject().react.trigger()

    def test_instance_attribute_trigger_without_reactors(self) -> None:
        Subject().react['subject_method'].react.trigger()

    def test_instance_attribute_trigger_with_instance_reactor(self) -> None:
        subject = Subject()
        with assert_reactor_called(subject):
            subject.react['subject_method'].react.trigger()

    def test_instance_attribute_trigger_with_instance_attribute_reactor(self) -> None:
        subject = Subject()
        with assert_reactor_called(subject.react['subject_method']):
            subject.react['subject_method'].react.trigger()


class TestInstanceAttributeDefinition:
    class InstanceAttributeDefinitionSubject(ReactiveInstance):
        @reactive_method
        def subject(self) -> None:
            pass

    class InheritedInstanceAttributeDefinitionSubject(InstanceAttributeDefinitionSubject):
        pass

    def test_iter_with_own_reactive_attribute(self) -> None:
        assert 1 == len(list(InstanceAttributeDefinition.iter(self.InstanceAttributeDefinitionSubject, 'subject')))

    def test_iter_with_inherited_reactive_attribute(self) -> None:
        assert 1 == len(list(InstanceAttributeDefinition.iter(self.InheritedInstanceAttributeDefinitionSubject, 'subject')))

    def test_iter_with_local_should_error(self) -> None:
        class Local(ReactiveInstance):
            pass

        with pytest.raises(ValueError):
            list(InstanceAttributeDefinition.iter(Local, 'local'))

    def test_register_with_local_should_error(self) -> None:
        def local() -> None:
            pass
        with pytest.raises(ValueError):
            InstanceAttributeDefinition(local)
