from __future__ import annotations

import copy
from contextlib import suppress
from typing import Any, Iterable

try:
    from typing import SupportsIndex  # type: ignore
except ImportError:
    from typing_extensions import SupportsIndex

from reactives import scope
from reactives.factory import Reactive
from reactives.reactor import ReactorController


class ReactiveDict(dict, Reactive):
    def __init__(self, *args, **kwargs):
        self.react = ReactorController()
        super().__init__(*args, **kwargs)
        for value in dict.values(self):
            self._wire(value)

    def __copy__(self) -> ReactiveDict:
        copied = self.__class__(self)
        copied.react = ReactorController()
        copied.react.react(*self.react.reactors)
        return copied

    def _wire(self, value) -> None:
        if isinstance(value, Reactive):
            value.react(self)

    def _unwire(self, value) -> None:
        if isinstance(value, Reactive):
            value.react.shutdown(self)

    def clear(self) -> None:
        for value in dict.values(self):
            self._unwire(value)
        super().clear()
        self.react.trigger()

    @scope.register_self
    def get(self, key):
        return super().get(key)

    @scope.register_self
    def items(self):
        return super().items()

    @scope.register_self
    def keys(self):
        return super().keys()

    def pop(self, key):
        value = super().pop(key)
        self._unwire(value)
        self.react.trigger()
        return value

    def popitem(self):
        key, value = super().popitem()
        self._unwire(value)
        self.react.trigger()
        return key, value

    def setdefault(self, key, value):
        try:
            return self[key]
        except KeyError:
            self[key] = value
            return value

    def update(self, *args, **kwargs) -> None:
        for value in super().values():
            self._unwire(value)
        super().update(*args, **kwargs)
        for value in super().values():
            self._wire(value)
        self.react.trigger()

    @scope.register_self
    def values(self):
        return super().values()

    @scope.register_self
    def __contains__(self, item):
        return super().__contains__(item)

    def __delitem__(self, key):
        with suppress(KeyError):
            self._unwire(super().__getitem__(key))
        super().__delitem__(key)
        self.react.trigger()

    @scope.register_self
    def __eq__(self, other):
        return super().__eq__(other)

    @scope.register_self
    def __getitem__(self, item):
        return super().__getitem__(item)

    @scope.register_self
    def __iter__(self):
        return super().__iter__()

    @scope.register_self
    def __len__(self):
        return super().__len__()

    @scope.register_self
    def __ne__(self, other):
        return super().__ne__(other)

    # dict.__reversed__() was added in Python 3.8.
    if hasattr(dict, '__reversed__'):
        @scope.register_self
        def __reversed__(self):
            # Mypy cannot tell we're only calling the parent method in Python >=3.8, so we have to suppress errors.
            return super().__reversed__()  # type: ignore

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._wire(value)
        # The reactor controller is not set in dict.__reduce__().
        with suppress(AttributeError):
            self.react.trigger()

    @scope.register_self
    def __sizeof__(self):
        return super().__sizeof__()


class ReactiveList(list, Reactive):
    def __init__(self, *args, **kwargs):
        self.react = ReactorController()
        super().__init__(*args, **kwargs)
        for value in list.__iter__(self):
            self._wire(value)

    def __copy__(self) -> ReactiveList:
        copied = self.__class__(self)
        scope.register(copied)
        copied.react = copy.copy(self.react)
        return copied

    def _wire(self, value) -> None:
        if isinstance(value, Reactive):
            value.react(self)

    def _unwire(self, value) -> None:
        if isinstance(value, Reactive):
            value.react.shutdown(self)

    def append(self, value) -> None:
        super().append(value)
        self._wire(value)
        self.react.trigger()

    def clear(self) -> None:
        for value in list.__iter__(self):
            self._unwire(value)
        super().clear()
        self.react.trigger()

    @scope.register_self
    def copy(self) -> ReactiveList:
        return copy.copy(self)

    @scope.register_self
    def count(self, value) -> int:
        return super().count(value)

    def extend(self, other: Iterable) -> None:
        for value in other:
            super().append(value)
            self._wire(value)
        # The reactor controller is not set in list.__reduce__().
        with suppress(AttributeError):
            self.react.trigger()

    @scope.register_self
    def index(self, value, *args, **kwargs) -> int:
        return super().index(value, *args, **kwargs)

    def insert(self, index: SupportsIndex, value: Any) -> None:
        super().insert(index, value)
        self._wire(value)
        self.react.trigger()

    def pop(self, *args, **kwargs) -> Any:
        value = super().pop(*args, **kwargs)
        self._unwire(value)
        self.react.trigger()
        return value

    def remove(self, value) -> None:
        super().remove(value)
        self._unwire(value)
        self.react.trigger()

    def reverse(self) -> None:
        super().reverse()
        self.react.trigger()

    def sort(self, *args, **kwargs) -> None:
        super().sort(*args, **kwargs)
        self.react.trigger()

    def __add__(self, other):
        return ReactiveList(super().__add__(other))

    @scope.register_self
    def __contains__(self, value) -> bool:
        return super().__contains__(value)

    def __delitem__(self, index) -> None:
        with suppress(IndexError):
            self._unwire(super().__getitem__(index))
        super().__delitem__(index)
        self.react.trigger()

    @scope.register_self
    def __eq__(self, other) -> bool:
        return super().__eq__(other)

    @scope.register_self
    def __getitem__(self, index) -> Any:
        return super().__getitem__(index)

    @scope.register_self
    def __iadd__(self, other: Iterable) -> ReactiveList:
        for value in other:
            super().append(value)
            self._wire(value)
        self.react.trigger()
        return self

    @scope.register_self
    def __imul__(self, other) -> ReactiveList:
        for value in list.__iter__(self):
            self._unwire(value)
        super().__imul__(other)
        for value in list.__iter__(self):
            self._wire(value)
        self.react.trigger()
        return self

    @scope.register_self
    def __iter__(self):
        return super().__iter__()

    @scope.register_self
    def __len__(self):
        return super().__len__()

    def __mul__(self, other):
        return ReactiveList(super().__mul__(other))

    @scope.register_self
    def __ne__(self, other):
        return super().__ne__(other)

    @scope.register_self
    def __reversed__(self):
        return super().__reversed__()

    def __rmul__(self, other):
        return ReactiveList(super().__rmul__(other))

    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self._wire(value)
        self.react.trigger()

    @scope.register_self
    def __sizeof__(self):
        return super().__sizeof__()
