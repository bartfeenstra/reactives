from typing import Any, Union, Callable

function = type(lambda: ())

# A reactive has an attribute called "react" containing a reactives.ReactorController.
# See reactives.assert_reactive() and reactives.is_reactive().
Reactive = Any

Reactor = Callable[[], None]

# A reactor definition is a reactor or anything that can be resolved to its reactors.
ReactorDefinition = Union[Reactor, Reactive]
