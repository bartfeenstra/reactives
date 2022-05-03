import copy
import pickle
from typing import Optional
from unittest import TestCase

from reactives import reactive, scope
from reactives import UnsupportedReactive
from reactives.factory.property import _PropertyReactorController
from reactives.factory.type import ReactiveInstance
from reactives.tests import assert_not_reactor_called, assert_reactor_called, assert_in_scope


class PropertyReactorControllerTest(TestCase):
    class Foo:
        @property
        def foo(self):
            return None

    def test___copy__(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            @reactive  # type: ignore
            @property
            def subject(self) -> None:
                return
        subject = Subject()
        sut = _PropertyReactorController(subject)
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    @reactive
    class _ReactiveProperty(ReactiveInstance):
        @reactive  # type: ignore
        @property
        def subject(self) -> None:
            return

    def test___getstate__(self) -> None:
        subject = self._ReactiveProperty()
        # Get the property so the instance can lazily instantiate the reactor controller we are testing here.
        subject.subject
        unpickled_subject = pickle.loads(pickle.dumps(subject))
        with assert_not_reactor_called(subject):
            with assert_reactor_called(unpickled_subject):
                unpickled_subject.react['subject'].react.trigger()


class ReactivePropertyTest(TestCase):
    def test_without_fget(self) -> None:
        with self.assertRaises(UnsupportedReactive):
            reactive(property())

    def test_fget(self) -> None:
        @reactive
        def dependency():
            pass

        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                super().__init__()
                self._subject_called = False

            @reactive  # type: ignore
            @property
            def subject(self):
                if not self._subject_called:
                    self._subject_called = True
                    return dependency()

        subject = Subject()

        with assert_in_scope(subject.react['subject']):
            # Call the reactive for the first time. This should result in dependency() being autowired.
            subject.subject

        with assert_reactor_called(subject):
            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

        # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
        with assert_in_scope(subject.react['subject']):
            subject.subject

        # dependency() no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            dependency.react.trigger()

    def test_fget_without_auto_collect_scope(self) -> None:
        @reactive
        def dependency():
            return 'Dependency'

        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                super().__init__()
                self._dependency = None

            @reactive(auto_collect_scope=False)  # type: ignore
            @property
            def subject(self):
                if not self._dependency:
                    with scope.collect(self.react['subject']):
                        self._dependency = dependency()
                return self._dependency

        subject = Subject()

        with assert_in_scope(subject.react['subject']):
            # Call the reactive for the first time. This should result in dependency() being autowired.
            subject.subject

        with assert_reactor_called(subject):
            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

        # Call the reactive again. This should result in the cached value being returned without being recomputed.
        subject.subject

        # Ensure that dependency() remains autowired even if the property's value is not recomputed.
        with assert_reactor_called(subject):
            dependency.react.trigger()

    def test_fset(self) -> None:
        @reactive
        class DependencyOne(ReactiveInstance):
            pass

        @reactive
        class DependencyTwo(ReactiveInstance):
            pass

        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                super().__init__()
                self._subject = 123

            @reactive  # type: ignore
            @property
            def subject(self):
                return self._subject

            @subject.setter
            def subject(self, subject) -> None:
                self._subject = subject

        subject = Subject()
        dependency_one = DependencyOne()
        dependency_two = DependencyTwo()

        # Setting dependency_one should cause the reactor to be called.
        with assert_reactor_called(subject.react['subject']):
            subject.subject = dependency_one
        self.assertEqual(dependency_one, subject.subject)

        # dependency_one being autowired should cause the reactor to be called.
        with assert_reactor_called(subject.react['subject']):
            dependency_one.react.trigger()

        # Setting dependency_two should cause the reactor to be called.
        with assert_reactor_called(subject.react['subject']):
            subject.subject = dependency_two
        self.assertEqual(dependency_two, subject.subject)

        # dependency_one no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject.react['subject']):
            dependency_one.react.trigger()

    def test_fdel(self) -> None:
        @reactive
        class Dependency(ReactiveInstance):
            pass

        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                self._subject: Optional[int] = 123

            @reactive  # type: ignore
            @property
            def subject(self):
                return self._subject

            @subject.setter
            def subject(self, subject) -> None:
                self._subject = subject

            @subject.deleter
            def subject(self) -> None:
                self._subject = None

        subject = Subject()

        # Even if the property's setter and getter weren't called, deletion should cause the reactor to be called.
        with assert_reactor_called(subject.react['subject']):
            del subject.subject
        self.assertIsNone(subject._subject)

        dependency = Dependency()

        # Setting dependency will autowire it.
        subject.subject = dependency

        # dependency_one no longer being autowired should not cause the reactor to be called.
        del subject.subject
        with assert_not_reactor_called() as reactor:
            subject.react['subject'].react.react_weakref(reactor)
        dependency.react.trigger()

    def test_on_trigger_delete_without_deleter(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                self._subject = 123

            @reactive  # type: ignore
            @property
            def subject(self):
                return self._subject

        subject = Subject()
        subject.react['subject'].react.trigger()
        self.assertEqual(123, subject._subject)

    def test_on_trigger_delete_with_deleter(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                self._subject: Optional[int] = 123

            @reactive  # type: ignore
            @property
            def subject(self):
                return self._subject

            @subject.deleter
            def subject(self) -> None:
                self._subject = None

        subject = Subject()
        subject.react['subject'].react.trigger()
        self.assertIsNone(subject._subject)

    def test_on_trigger_delete_with_deleter_but_on_trigger_delete_is_false(self) -> None:
        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                self._subject: Optional[int] = 123

            @reactive(on_trigger_delete=False)  # type: ignore
            @property
            def subject(self):
                return self._subject

            @subject.deleter
            def subject(self) -> None:
                self._subject = None

        subject = Subject()
        subject.react['subject'].react.trigger()
        self.assertEqual(123, subject._subject)
