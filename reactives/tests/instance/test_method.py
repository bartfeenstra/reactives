from reactives.function import reactive_function
from reactives.instance import ReactiveInstance
from reactives.instance.method import reactive_method
from reactives.tests import assert_reactor_called, assert_not_reactor_called


@reactive_function
def dependency() -> None:
    pass


class Subject(ReactiveInstance):
    def __init__(self) -> None:
        super().__init__()
        self.called = False

    @reactive_method
    def subject(self) -> None:
        if not self.called:
            self.called = True
            dependency()


class SubjectWithOnTriggerCall(ReactiveInstance):
    def __init__(self) -> None:
        super().__init__()
        self.on_trigger_calls = 0

    @reactive_method(on_trigger_call=True)
    def subject(self) -> None:
        self.on_trigger_calls += 1


class TestReactiveMethod:
    def test_wrapped_metadata_for_class_method(self) -> None:
        assert 'reactives.tests.instance.test_method' == Subject.subject.__module__
        assert 'subject' == Subject.subject.__name__
        assert 'Subject.subject' == Subject.subject.__qualname__

    def test_wrapped_metadata_for_instance_method(self) -> None:
        assert 'reactives.tests.instance.test_method' == Subject().subject.__module__
        assert 'subject' == Subject().subject.__name__
        assert 'Subject.subject' == Subject().subject.__qualname__

    def test_call_as_class_method(self) -> None:
        subject = Subject()
        # Call the reactive for the first time. This should result in dependency() being autowired.
        Subject.subject(subject)
        # dependency() being autowired should cause the reactor to be called.
        with assert_reactor_called(subject):
            dependency.react.trigger()
        # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
        Subject.subject(subject)
        # dependency() no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            dependency.react.trigger()

    def test_call_as_instance_method(self) -> None:
        subject = Subject()
        # Call the reactive for the first time. This should result in dependency() being autowired.
        subject.subject()
        # dependency() being autowired should cause the reactor to be called.
        with assert_reactor_called(subject):
            dependency.react.trigger()
        # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
        subject.subject()
        # dependency() no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            dependency.react.trigger()

    def test_on_trigger_call(self) -> None:
        subject = SubjectWithOnTriggerCall()
        subject.react['subject'].react.trigger()
        assert subject.on_trigger_calls == 1
