from __future__ import annotations

import copy
from contextlib import suppress
from typing import Any, Iterable, TypeVar, Generic, Optional, overload, Iterator, List, cast, Dict, SupportsIndex

from reactives import scope
from reactives.factory import Reactive
from reactives.reactor import ReactorController

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

T = TypeVar('T')
KeyT = TypeVar('KeyT')
ValueT = TypeVar('ValueT')


class ReactiveDict(Dict[KeyT, ValueT], Reactive, Generic[KeyT, ValueT]):
    def __init__(self, *args, **kwargs):
        self.react = ReactorController()
        super().__init__(*args, **kwargs)
        for value in dict.values(self):
            self._wire(value)

    def __copy__(self) -> Self:
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

    @overload
    def setdefault(self, key: KeyT) -> Optional[ValueT]:
        pass

    @overload
    def setdefault(self, key: KeyT, value: ValueT) -> ValueT:
        pass

    def setdefault(self, key: KeyT, value: Optional[ValueT] = None) -> Optional[ValueT]:
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

    @scope.register_self
    def __reversed__(self):
        return super().__reversed__()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._wire(value)
        # The reactor controller is not set in dict.__reduce__().
        with suppress(AttributeError):
            self.react.trigger()

    @scope.register_self
    def __sizeof__(self):
        return super().__sizeof__()


class ReactiveList(List[ValueT], Reactive):
    def __init__(self, *args, **kwargs):
        self.react = ReactorController()
        super().__init__(*args, **kwargs)
        self._wire(*list.__iter__(self))

    def __copy__(self) -> Self:
        copied = self.__class__(self)
        scope.register(copied)
        copied.react = copy.copy(self.react)
        return copied

    def _wire(self, *values: ValueT) -> None:
        for value in values:
            if isinstance(value, Reactive):
                value.react(self)

    def _unwire(self, *values: ValueT) -> None:
        for value in values:
            if isinstance(value, Reactive):
                value.react.shutdown(self)

    def append(self, value: ValueT) -> None:
        super().append(value)
        self._wire(value)
        self.react.trigger()

    def clear(self) -> None:
        self._unwire(*list.__iter__(self))
        super().clear()
        self.react.trigger()

    @scope.register_self
    def copy(self) -> ReactiveList:
        return copy.copy(self)

    @scope.register_self
    def count(self, value: ValueT) -> int:
        return super().count(value)

    def extend(self, other: Iterable[ValueT]) -> None:
        for value in other:
            super().append(value)
            self._wire(value)
        # The reactor controller is not set in list.__reduce__().
        with suppress(AttributeError):
            self.react.trigger()

    @scope.register_self
    def index(self, value: ValueT, *args, **kwargs) -> int:
        return super().index(value, *args, **kwargs)

    def insert(self, index: SupportsIndex, value: ValueT) -> None:
        super().insert(index, value)
        self._wire(value)
        self.react.trigger()

    def pop(self, *args, **kwargs) -> ValueT:
        value = super().pop(*args, **kwargs)
        self._unwire(value)
        self.react.trigger()
        return value

    def remove(self, value: ValueT) -> None:
        super().remove(value)
        self._unwire(value)
        self.react.trigger()

    def reverse(self) -> None:
        super().reverse()
        self.react.trigger()

    def sort(self, *args, **kwargs) -> None:
        super().sort(*args, **kwargs)
        self.react.trigger()

    @overload
    def __add__(self, other: List[ValueT]) -> Self:
        pass

    @overload
    def __add__(self, other: List[T]) -> ReactiveList[ValueT | T]:
        pass

    def __add__(  # type: ignore
        self,
        other: List[ValueT] | List[T],
    ) -> Self | ReactiveList[ValueT | T]:
        return ReactiveList(super().__add__(other))

    @scope.register_self
    def __contains__(self, value: Any) -> bool:
        return super().__contains__(value)

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        with suppress(IndexError):
            if isinstance(index, slice):
                self._unwire(*super().__getitem__(index))
            else:
                self._unwire(super().__getitem__(index))
        super().__delitem__(index)
        self.react.trigger()

    @scope.register_self
    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)

    @scope.register_self
    def __getitem__(self, index: SupportsIndex) -> Any:
        return super().__getitem__(index)

    @scope.register_self
    def __iadd__(self, other: Iterable[ValueT]) -> Self:
        for value in other:
            super().append(value)
            self._wire(value)
        self.react.trigger()
        return self

    @scope.register_self
    def __imul__(self, other) -> ReactiveList:
        self._unwire(*list.__iter__(self))
        super().__imul__(other)
        self._wire(*list.__iter__(self))
        self.react.trigger()
        return self

    @scope.register_self
    def __iter__(self) -> Iterator[ValueT]:
        return super().__iter__()

    @scope.register_self
    def __len__(self) -> int:
        return super().__len__()

    def __mul__(self, other: SupportsIndex) -> Self:
        return type(self)(super().__mul__(other))

    @scope.register_self
    def __ne__(self, other: Any) -> bool:
        return super().__ne__(other)

    @scope.register_self
    def __reversed__(self) -> Self:
        return type(self)(super().__reversed__())

    def __rmul__(self, other: SupportsIndex) -> Self:
        return type(self)(super().__rmul__(other))

    @overload
    def __setitem__(self, index: SupportsIndex, value: ValueT) -> None:
        pass

    @overload
    def __setitem__(self, index: slice, value: Iterable[ValueT]) -> None:
        pass

    def __setitem__(self, index: SupportsIndex | slice, value: ValueT | Iterable[ValueT]) -> None:
        if isinstance(index, slice):
            super().__setitem__(index, cast(Iterable[ValueT], value))
            self._wire(*cast(Iterable[ValueT], value))
        else:
            super().__setitem__(index, cast(ValueT, value))
            self._wire(cast(ValueT, value))
        self.react.trigger()

    @scope.register_self
    def __sizeof__(self) -> int:
        return super().__sizeof__()
