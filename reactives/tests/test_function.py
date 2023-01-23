from reactives.function import reactive_function
from reactives.tests import assert_reactor_called, assert_not_reactor_called


@reactive_function
def dependency() -> None:
    pass


@reactive_function
def subject() -> None:
    pass


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
        called = False

        @reactive_function
        def subject() -> None:
            nonlocal called
            if not called:
                called = True
                dependency()

        # Call the reactive for the first time. This should result in dependency() being autowired.
        subject()
        # dependency() being autowired should cause the reactor to be called.
        with assert_reactor_called(subject):
            dependency.react.trigger()
        # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
        subject()
        # dependency() no longer being autowired should not cause the reactor to be called.
        with assert_not_reactor_called(subject):
            dependency.react.trigger()

    def test_on_trigger_call(self) -> None:
        global _on_trigger_calls

        assert _on_trigger_calls == 0
        subject_with_on_trigger_call.react.trigger()
        assert _on_trigger_calls == 1
        _on_trigger_calls = 0
