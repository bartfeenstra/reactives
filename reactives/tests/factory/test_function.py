import copy
import pickle
from unittest import TestCase

from reactives import reactive
from reactives.factory.function import _FunctionReactorController
from reactives.factory.type import ReactiveInstance
from reactives.tests import assert_reactor_called, assert_not_reactor_called


class ReactiveFunctionControllerTest(TestCase):
    def test___copy__(self) -> None:
        @reactive
        def subject():
            pass
        sut = _FunctionReactorController()
        with assert_reactor_called(sut):
            copied_sut = copy.copy(sut)
            with assert_not_reactor_called(sut):
                with assert_reactor_called(copied_sut):
                    copied_sut.trigger()

    @reactive
    class _Reactive(ReactiveInstance):
        @reactive
        def subject(self) -> None:
            pass

    def test___getstate__(self) -> None:
        subject = self._Reactive()
        # Call the function so the instance can lazily instantiate the reactor controller we are testing here.
        subject.subject()
        unpickled_subject = pickle.loads(pickle.dumps(subject))
        with assert_not_reactor_called(subject):
            with assert_reactor_called(unpickled_subject):
                unpickled_subject.react['subject'].react.trigger()


class ReactiveFunctionTest(TestCase):
    def test_without_reactors(self) -> None:
        @reactive
        def subject():
            subject.tracker.append(True)
        subject.tracker = []
        subject()
        self.assertEqual([True], subject.tracker)

    def test_with_reactor(self) -> None:
        @reactive
        def subject():
            raise AssertionError('This function should not have been called.')

        with assert_reactor_called(subject):
            subject.react.trigger()

    def test_with_reactor_and_dependency(self) -> None:
        @reactive
        def dependency():
            pass

        @reactive
        def subject():
            if not subject.called:
                subject.called = True
                dependency()
        subject.called = False
        with assert_reactor_called(subject):
            # Call the reactive for the first time. This should result in dependency() being autowired.
            subject()
            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

            # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
            subject()
            # dependency() no longer being autowired should not cause the reactor to be called.
            dependency.react.trigger()

    def test_with_reactor_and_dependency_as_instance_method(self) -> None:
        @reactive
        def dependency():
            pass

        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                self.called = False

            @reactive
            def subject(self):
                if not self.called:
                    self.called = True
                    dependency()
        subject = Subject()
        with assert_reactor_called(subject):
            # Call the reactive for the first time. This should result in dependency() being autowired.
            subject.subject()
            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

            # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
            subject.subject()
            # dependency() no longer being autowired should not cause the reactor to be called.
            dependency.react.trigger()

    def test_on_trigger_call(self):
        @reactive(on_trigger_call=True)
        def subject():
            subject.tracker.append(True)
        subject.tracker = []
        subject.react.trigger()
        self.assertEqual([True], subject.tracker)

    def test_on_trigger_call_as_instance_method(self):
        @reactive
        class Subject(ReactiveInstance):
            def __init__(self):
                self.tracker = []

            @reactive(on_trigger_call=True)
            def subject(self):
                self.tracker.append(True)
        subject = Subject()
        subject.react['subject'].react.trigger()
        self.assertEqual([True], subject.tracker)
