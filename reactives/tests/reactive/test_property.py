import pickle
from unittest import TestCase

from reactives import reactive
from reactives import UnsupportedReactive
from reactives.tests import assert_not_reactor_called, assert_reactor_called, assert_in_scope


class ReactivePropertyReactorControllerTest(TestCase):
    @reactive
    class _ReactiveProperty:
        @reactive
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
                unpickled_subject.react.getattr('subject').react.trigger()


class ReactivePropertyTest(TestCase):
    def test_without_fget(self) -> None:
        with self.assertRaises(UnsupportedReactive):
            reactive(property())

    def test_fget(self) -> None:
        @reactive
        def dependency():
            pass

        @reactive
        class Subject:
            def __init__(self):
                self._subject_called = False

            @reactive
            @property
            def subject(self):
                if not self._subject_called:
                    self._subject_called = True
                    return dependency()

            @reactive
            @property
            def subject2(self):
                if not self._subject_called:
                    self._subject_called = True
                    return dependency()

        subject = Subject()

        with assert_reactor_called(subject):
            with assert_in_scope(subject.react.getattr('subject')):
                # Call the reactive for the first time. This should result in dependency() being autowired.
                subject.subject

            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

            # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
            with assert_in_scope(subject.react.getattr('subject')):
                subject.subject

        # dependency() no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            dependency.react.trigger()

    def test_fset(self) -> None:
        @reactive
        class DependencyOne:
            pass

        @reactive
        class DependencyTwo:
            pass

        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive
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
        with assert_reactor_called(subject.react.getattr('subject')):
            subject.subject = dependency_one
            self.assertEquals(dependency_one, subject._subject)

        # dependency_one being autowired should cause the reactor to be called.
        with assert_reactor_called(subject.react.getattr('subject')):
            dependency_one.react.trigger()

        # Setting dependency_two should cause the reactor to be called.
        with assert_reactor_called(subject.react.getattr('subject')):
            subject.subject = dependency_two
            self.assertEquals(dependency_two, subject._subject)

        # dependency_one no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject.react.getattr('subject')):
            dependency_one.react.trigger()

    def test_fdel(self) -> None:
        @reactive
        class Dependency:
            pass

        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive
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
        with assert_reactor_called(subject.react.getattr('subject')):
            del subject.subject
        self.assertIsNone(subject._subject)

        dependency = Dependency()

        # Setting dependency will autowire it.
        subject.subject = dependency

        # dependency_one no longer being autowired should not cause the reactor to be called.
        del subject.subject
        subject.react.getattr('subject').react.react_weakref(
            assert_not_reactor_called())
        dependency.react.trigger()

    def test_on_trigger_delete_without_deleter(self) -> None:
        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive
            @property
            def subject(self):
                return self._subject

        subject = Subject()
        subject.react.getattr('subject').react.trigger()
        self.assertEqual(123, subject._subject)

    def test_on_trigger_delete_with_deleter(self) -> None:
        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive
            @property
            def subject(self):
                return self._subject

            @subject.deleter
            def subject(self) -> None:
                self._subject = None

        subject = Subject()
        subject.react.getattr('subject').react.trigger()
        self.assertIsNone(subject._subject)

    def test_on_trigger_delete_with_deleter_but_on_trigger_delete_is_false(self) -> None:
        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive(on_trigger_delete=False)
            @property
            def subject(self):
                return self._subject

            @subject.deleter
            def subject(self) -> None:
                self._subject = None

        subject = Subject()
        subject.react.getattr('subject').react.trigger()
        self.assertEqual(123, subject._subject)
