from reactives.function import reactive_function
from reactives.instance import ReactiveInstance
from reactives.instance.method import reactive_method
from reactives.tests import assert_reactor_called, assert_not_reactor_called


@reactive_function
def dependency_one() -> None:
    dependency_two()


@reactive_function
def dependency_two() -> None:
    pass


class Subject(ReactiveInstance):
    @reactive_method
    def subject(self, call_dependency: bool) -> None:
        if call_dependency:
            dependency_one()


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

        # Call the reactive for the first time. This should result in dependency_one() being autowired to
        # subject.subject()
        Subject.subject(subject, True)

        # dependency_one() being autowired to subject.subject() should cause subject.subject() to be triggered.
        with assert_reactor_called(subject.react['subject']):
            dependency_one.react.trigger()

        # dependency_two() being autowired to dependency_one() should cause subject.subject() and dependency_one() to be
        # triggered.
        with assert_reactor_called(subject.react['subject']):
            with assert_reactor_called(dependency_one):
                dependency_two.react.trigger()

        # Ensure that dependencies are only added to the direct calling scope, and not to ancestors' scopes.
        assert dependency_one.react in list(dependency_two.react._reactors)

        # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
        Subject.subject(subject, False)

        # dependency_one() no longer being autowired should not cause subject.subject() to be triggered.
        with assert_not_reactor_called(subject.react['subject']):
            dependency_one.react.trigger()

    def test_call_as_instance_method(self) -> None:
        subject = Subject()

        # Call the reactive for the first time. This should result in dependency_one() being autowired to
        # subject.subject()
        subject.subject(True)

        # dependency_one() being autowired to subject.subject() should cause subject.subject() to be triggered.
        with assert_reactor_called(subject.react['subject']):
            dependency_one.react.trigger()

        # dependency_two() being autowired to dependency_one() should cause subject.subject() and dependency_one() to be
        # triggered.
        with assert_reactor_called(subject.react['subject']):
            with assert_reactor_called(dependency_one):
                dependency_two.react.trigger()

        # Ensure that dependencies are only added to the direct calling scope, and not to ancestors' scopes.
        assert dependency_one.react in list(dependency_two.react._reactors)

        # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
        subject.subject(False)

        # dependency_one() no longer being autowired should not cause subject.subject() to be triggered.
        with assert_not_reactor_called(subject.react['subject']):
            dependency_one.react.trigger()

    def test_on_trigger_call(self) -> None:
        subject = SubjectWithOnTriggerCall()
        subject.react['subject'].react.trigger()
        assert subject.on_trigger_calls == 1
