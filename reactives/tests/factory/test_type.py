from __future__ import annotations

import copy
import pickle
from unittest import TestCase

from reactives.factory import reactive, Reactive
from reactives.factory.type import _InstanceReactorController, ReactiveInstance
from reactives.tests import assert_reactor_called, assert_not_reactor_called


class InstanceReactorControllerTest(TestCase):
    def test___copy__(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            pass
        sut = _InstanceReactorController(Subject())
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    def test_getattr_with_reactive_attribute(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            @reactive
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        self.assertIsInstance(sut.getattr('subject'), Reactive)

    def test_getattr_with_non_existent_reactive_attribute(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        with self.assertRaises(AttributeError):
            sut.getattr('subject')

    def test___getitem___with_reactive_attribute(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            @reactive
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        self.assertIsInstance(sut['subject'], Reactive)

    def test___getitem___with_non_existent_reactive_attribute(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        with self.assertRaises(AttributeError):
            sut['subject']


class ReactiveTypeTest(TestCase):
    @reactive
    class Subject(ReactiveInstance):
        @reactive
        def subject_function(self) -> None:
            pass

        @reactive  # type: ignore
        @property
        def subject_property(self) -> None:
            return

    @reactive
    class SubjectWithCopy(Subject):
        def __copy__(self) -> ReactiveTypeTest.SubjectWithCopy:
            return self.__class__()

    def test_pickle(self) -> None:
        subject = self.Subject()
        unpickled_subject = pickle.loads(pickle.dumps(subject))
        with assert_not_reactor_called(subject):
            with assert_reactor_called(unpickled_subject):
                unpickled_subject.react.trigger()

    def test___copy___without___copy__(self) -> None:
        subject = self.Subject()
        copied_subject = copy.copy(subject)
        with assert_not_reactor_called(subject):
            with assert_reactor_called(copied_subject):
                copied_subject.react.trigger()

    def test___copy___with___copy__(self) -> None:
        subject = self.SubjectWithCopy()
        copied_subject = copy.copy(subject)
        with assert_not_reactor_called(subject):
            with assert_reactor_called(copied_subject):
                copied_subject.react.trigger()

    def test_instance_trigger_without_reactors(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            pass
        Subject().react.trigger()

    def test_instance_trigger_with_instance_reactor(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            pass
        subject = Subject()
        with assert_reactor_called(subject):
            subject.react.trigger()

    def test_instance_trigger_with_instance_attribute_reactor(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with assert_not_reactor_called(subject.react['subject']):
            Subject().react.trigger()

    def test_instance_attribute_trigger_without_reactors(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            @reactive
            def subject(self) -> None:
                pass
        Subject().react['subject'].react.trigger()

    def test_instance_attribute_trigger_with_instance_reactor(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with assert_reactor_called(subject):
            subject.react['subject'].react.trigger()

    def test_instance_attribute_trigger_with_instance_attribute_reactor(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with assert_reactor_called(subject.react['subject']):
            subject.react['subject'].react.trigger()

    def test_without_subclass_should_warn(self) -> None:
        with self.assertWarns(UserWarning):
            @reactive
            class Subject:
                pass
