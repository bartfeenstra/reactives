from unittest import TestCase

from reactives.reactive import reactive
from reactives.tests import assert_reactor_called


class ReactiveFunctionTest(TestCase):
    def test_without_reactors(self) -> None:
        @reactive
        def subject():
            subject.tracker.append(True)
        subject.tracker = []
        subject()
        self.assertEquals([True], subject.tracker)

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

    def test_on_trigger_call(self):
        @reactive(on_trigger_call=True)
        def subject():
            subject.tracker.append(True)
        subject.tracker = []
        subject.react.trigger()
        self.assertEquals([True], subject.tracker)

    def test_on_trigger_call_as_instance_method(self):
        @reactive
        class Subject:
            def __init__(self):
                self.tracker = []

            @reactive(on_trigger_call=True)
            def subject(self):
                self.tracker.append(True)
        subject = Subject()
        subject.react.getattr('subject').react.trigger()
        self.assertEquals([True], subject.tracker)
