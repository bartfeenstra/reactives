from reactives.function import reactive_function
from reactives.tests import assert_reactor_called, assert_not_reactor_called


@reactive_function
def dependency_one() -> None:
    dependency_two()


@reactive_function
def dependency_two() -> None:
    pass


@reactive_function
def subject(call_dependency: bool) -> None:
    if call_dependency:
        dependency_one()


_on_trigger_calls = 0


@reactive_function(on_trigger_call=True)
def subject_with_on_trigger_call() -> None:
    global _on_trigger_calls
    _on_trigger_calls += 1


class TestReactiveFunction:
    def test_wrapped_metadata(self) -> None:
        assert 'reactives.tests.test_function' == subject.__module__
        assert 'subject' == subject.__name__
        assert 'subject' == subject.__qualname__

    def test_call(self) -> None:
        # Call the reactive for the first time. This should result in dependency_one() being autowired to subject().
        subject(True)

        # dependency_one() being autowired to subject() should cause subject() to be triggered.
        with assert_reactor_called(subject):
            dependency_one.react.trigger()

        # dependency_two() being autowired to dependency_one() should cause subject() and dependency_one() to be
        # triggered.
        with assert_reactor_called(subject):
            with assert_reactor_called(dependency_one):
                dependency_two.react.trigger()

        # Ensure that dependencies are only added to the direct calling scope, and not to ancestors' scopes.
        assert dependency_one.react in list(dependency_two.react._reactors)

        # Call the reactive again. This should result in dependency_*() being ignored and not to be autowired again.
        subject(False)
        # dependency_one() and dependency_two() no longer being autowired should not cause subject() to be triggered().
        with assert_not_reactor_called(subject):
            dependency_one.react.trigger()
            dependency_two.react.trigger()

    def test_on_trigger_call(self) -> None:
        global _on_trigger_calls

        assert _on_trigger_calls == 0
        subject_with_on_trigger_call.react.trigger()
        assert _on_trigger_calls == 1
        _on_trigger_calls = 0
