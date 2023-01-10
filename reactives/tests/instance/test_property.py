from __future__ import annotations

import copy
import pickle
from typing import cast
from unittest import TestCase

from parameterized import parameterized

from reactives.function import reactive_function
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property, OnTriggerDelete, _PropertyReactorController
from reactives.tests import assert_not_reactor_called, assert_reactor_called


@reactive_function
def dependency() -> None:
    pass


class DependencyOne(ReactiveInstance):
    pass


class DependencyTwo(ReactiveInstance):
    pass


class Subject(ReactiveInstance):
    def __init__(self, subject: ReactiveInstance | int | None = None):
        super().__init__()
        self._subject: ReactiveInstance | int | None = subject

    @property
    @reactive_property
    def subject(self) -> ReactiveInstance | int | None:
        return self._subject


class SubjectWithSetter(Subject):
    @property
    @reactive_property
    def subject(self) -> ReactiveInstance | int | None:
        return self._subject

    @subject.setter
    def subject(self, subject: ReactiveInstance | int | None) -> None:
        self._subject = subject


class SubjectWithDeleter(Subject):
    @property
    @reactive_property
    def subject(self) -> ReactiveInstance | int | None:
        return self._subject

    @subject.deleter
    def subject(self) -> None:
        self._subject = None


class PropertyReactorControllerTest(TestCase):
    def test___copy__(self) -> None:
        subject = Subject()
        sut = subject.react.getattr_reactive('subject').react
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    def test___getstate__(self) -> None:
        subject = Subject()
        # Get the property so the instance can lazily instantiate the reactor controller we are testing here.
        subject.subject
        unpickled_subject = pickle.loads(pickle.dumps(subject))
        with assert_not_reactor_called(subject):
            with assert_reactor_called(unpickled_subject):
                unpickled_subject.react['subject'].react.trigger()

    class _Subject(ReactiveInstance):
        def __init__(self) -> None:
            super().__init__()
            self._subject: int | None = 123

    class _SubjectWithOnTriggerDeleteIsNoDelete(_Subject):
        def __init__(self) -> None:
            super().__init__()
            self._subject: int | None = 123

        @property
        @reactive_property(on_trigger_delete=OnTriggerDelete.NO_DELETE)
        def subject(self) -> int | None:
            return self._subject

    class _SubjectWithOnTriggerDeleteIsDeleteIfDeletable(_Subject):
        def __init__(self) -> None:
            super().__init__()
            self._subject: int | None = 123

        @property
        @reactive_property(on_trigger_delete=OnTriggerDelete.DELETE_IF_DELETABLE)
        def subject(self) -> int | None:
            return self._subject

    class _SubjectWithOnTriggerDeleteIsDelete(_Subject):
        def __init__(self) -> None:
            super().__init__()
            self._subject: int | None = 123

        @property
        @reactive_property(on_trigger_delete=OnTriggerDelete.DELETE)
        def subject(self) -> int | None:
            return self._subject

    class _SubjectWithOnTriggerDeleteIsNoDeleteWithDeleter(_Subject):
        def __init__(self) -> None:
            super().__init__()
            self._subject: int | None = 123

        @property
        @reactive_property(on_trigger_delete=OnTriggerDelete.NO_DELETE)
        def subject(self) -> int | None:
            return self._subject

        @subject.deleter
        def subject(self) -> None:
            self._subject = None

    class _SubjectWithOnTriggerDeleteIsDeleteIfDeletableWithDeleter(_Subject):
        def __init__(self) -> None:
            super().__init__()
            self._subject: int | None = 123

        @property
        @reactive_property(on_trigger_delete=OnTriggerDelete.DELETE_IF_DELETABLE)
        def subject(self) -> int | None:
            return self._subject

        @subject.deleter
        def subject(self) -> None:
            self._subject = None

    class _SubjectWithOnTriggerDeleteIsDeleteWithDeleter(_Subject):
        @property
        @reactive_property(on_trigger_delete=OnTriggerDelete.DELETE)
        def subject(self) -> int | None:
            return self._subject

        @subject.deleter
        def subject(self) -> None:
            self._subject = None

    @parameterized.expand([
        (123, _SubjectWithOnTriggerDeleteIsNoDeleteWithDeleter()),
        (None, _SubjectWithOnTriggerDeleteIsDeleteIfDeletableWithDeleter()),
        (None, _SubjectWithOnTriggerDeleteIsDeleteWithDeleter()),
        (123, _SubjectWithOnTriggerDeleteIsNoDelete()),
        (123, _SubjectWithOnTriggerDeleteIsDeleteIfDeletable()),
    ])
    def test_on_trigger_delete(
        self,
        expected_property_value: int | None,
        subject: Subject,
    ) -> None:
        cast(_PropertyReactorController, subject.react['subject'].react).trigger()
        self.assertEqual(expected_property_value, subject.subject)


class ReactivePropertyTest(TestCase):
    class SubjectWithGetterDependency(ReactiveInstance):
        def __init__(self) -> None:
            super().__init__()
            self._subject_called = False

        @property
        @reactive_property
        def subject(self) -> None:
            if not self._subject_called:
                self._subject_called = True
                dependency()
            return None

    def test_getter(self) -> None:
        subject = self.SubjectWithGetterDependency()

        # Call the reactive for the first time. This should result in dependency() being autowired.
        subject.subject

        with assert_reactor_called(subject):
            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

        # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
        subject.subject

        # dependency() no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            dependency.react.trigger()

    def test_setter(self) -> None:
        subject = SubjectWithSetter()
        dependency_one = DependencyOne()
        dependency_two = DependencyTwo()

        # Setting dependency_one should cause the reactor to be called.
        with assert_reactor_called(subject):
            with assert_reactor_called(subject.react['subject']):
                subject.subject = dependency_one
        self.assertEqual(dependency_one, subject.subject)

        # dependency_one being autowired should cause the reactor to be called.
        with assert_reactor_called(subject):
            with assert_reactor_called(subject.react['subject']):
                dependency_one.react.trigger()

        # Setting dependency_two should cause the reactor to be called.
        with assert_reactor_called(subject):
            with assert_reactor_called(subject.react['subject']):
                subject.subject = dependency_two
        self.assertEqual(dependency_two, subject.subject)

        # dependency_one no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            with assert_not_reactor_called(subject.react['subject']):
                dependency_one.react.trigger()

    def test_deleter(self) -> None:
        dependency_one = DependencyOne()
        subject = SubjectWithDeleter(dependency_one)

        with assert_reactor_called(subject):
            with assert_reactor_called(subject.react['subject']):
                del subject.subject
        self.assertIsNone(subject._subject)

        # dependency_one no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            with assert_not_reactor_called(subject.react['subject']):
                dependency.react.trigger()
