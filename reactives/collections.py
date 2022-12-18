from __future__ import annotations

from contextlib import suppress
from typing import Any, Iterable, TypeVar, Generic, overload, Iterator, cast, Tuple, ValuesView, KeysView, \
    ItemsView, TYPE_CHECKING, List, Dict, Mapping, Reversible, MutableMapping, Sequence, MutableSequence

from reactives import scope, Reactive
from reactives.reactor import ReactorController

try:
    from typing_extensions import Self
except ImportError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover

if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem  # pragma: no cover


T = TypeVar('T')
KeyT = TypeVar('KeyT')
ValueT = TypeVar('ValueT')
ValueTCov = TypeVar('ValueTCov', covariant=True)


class _ReactiveCollection(Reactive):
    def _wire(self, *values: Any) -> None:
        for value in values:
            if isinstance(value, Reactive):
                value.react(self)

    def _unwire(self, *values: Any) -> None:
        for value in values:
            if isinstance(value, Reactive):
                value.react.shutdown(self)

    def __copy__(self) -> Self:
        copied = self.__class__(self)
        copied.react.react(*self.react._reactors)
        return copied


class ReactiveMapping(Mapping[KeyT, ValueTCov], _ReactiveCollection, Reversible, Generic[KeyT, ValueTCov]):
    def __init__(
        self,
        other: SupportsKeysAndGetItem[KeyT, ValueTCov] | Iterable[Tuple[KeyT, ValueTCov]] | None = None,
        **kwargs: ValueTCov,
    ) -> None:
        self.react = ReactorController()
        super().__init__()
        # Specifically use a dictionary, because those are ordered.
        self._values: Dict[KeyT, ValueTCov] = {}
        args = () if other is None else (other,)
        self._values.update(*args, **kwargs)
        for value in self._values.values():
            self._wire(value)

    @overload
    def get(self, key: KeyT) -> ValueTCov | None:
        pass

    @overload
    def get(self, key: KeyT, default: ValueTCov | T) -> ValueTCov | T:
        pass

    @scope.register_self  # type: ignore[misc]
    def get(
            self,
            key: KeyT,
            default: ValueTCov | T | None = None,
    ) -> ValueTCov | T | None:
        if default is None:
            return super().get(key)
        return super().get(key, default)

    @scope.register_self
    def items(self) -> ItemsView[KeyT, ValueTCov]:
        return self._values.items()

    @scope.register_self
    def keys(self) -> KeysView[KeyT]:
        return self._values.keys()

    @scope.register_self
    def values(self) -> ValuesView[ValueTCov]:
        return self._values.values()

    @scope.register_self
    def __contains__(self, item: Any) -> bool:
        return item in self._values

    @scope.register_self
    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)

    @scope.register_self
    def __getitem__(self, key: KeyT) -> ValueTCov:
        return self._values[key]

    @scope.register_self
    def __iter__(self) -> Iterator[KeyT]:
        yield from self._values

    @scope.register_self
    def __len__(self) -> int:
        return len(self._values)

    @scope.register_self
    def __ne__(self, other: Any) -> bool:
        return super().__ne__(other)

    @scope.register_self
    def __reversed__(self) -> Iterator[KeyT]:
        yield from reversed(self._values)


class ReactiveMutableMapping(ReactiveMapping[KeyT, ValueT], MutableMapping[KeyT, ValueT], Generic[KeyT, ValueT]):
    def clear(self) -> None:
        self._unwire(*self._values.values())
        self._values.clear()
        self.react.trigger()

    @overload
    def pop(self, key: KeyT) -> ValueT:
        pass

    @overload
    def pop(self, key: KeyT, default: ValueT | T) -> ValueT | T:
        pass

    def pop(  # type: ignore[misc]
            self,
            key: KeyT,
            default: ValueT | T | None = None,
    ) -> ValueT | T:
        args = () if default is None else (default,)
        value = self._values.pop(key, *args)
        self._unwire(value)
        self.react.trigger()
        return value

    def popitem(self) -> Tuple[KeyT, ValueT]:
        key, value = self._values.popitem()
        self._unwire(value)
        self.react.trigger()
        return key, value

    @overload
    def setdefault(self, key: KeyT) -> ValueT | None:
        pass

    @overload
    def setdefault(self, key: KeyT, value: ValueT) -> ValueT:
        pass

    def setdefault(self, key: KeyT, value: ValueT | None = None) -> ValueT | None:
        try:
            return self[key]
        except KeyError:
            self[key] = cast(ValueT, value)
            return value

    def update(
        self,
        other: SupportsKeysAndGetItem[KeyT, ValueT] | Iterable[Tuple[KeyT, ValueT]] | None = None,
        /,
        **kwargs: ValueT,
    ) -> None:
        args = () if other is None else (other,)
        self._values.update(*args, **kwargs)
        for value in self._values.values():
            self._wire(value)
        self.react.trigger()

    def __delitem__(self, key: KeyT) -> None:
        with suppress(KeyError):
            self._unwire(self._values[key])
        del self._values[key]
        self.react.trigger()

    def __setitem__(self, key: KeyT, value: ValueT) -> None:
        self._values[key] = value
        self._wire(value)
        self.react.trigger()


class ReactiveSequence(Sequence[ValueTCov], _ReactiveCollection, Generic[ValueTCov]):
    def __init__(self, other: Iterable[ValueTCov] | None = None):
        self.react = ReactorController()
        super().__init__()
        self._values: List[ValueTCov] = []
        if other is not None:
            for value in other:
                self._values.append(value)
                self._wire(value)

    @scope.register_self
    def count(self, value: Any) -> int:
        return super().count(value)

    @scope.register_self
    def index(self, value: Any, start: int | None = None, stop: int | None = None) -> int:
        args = [value]
        if start is not None:
            args.append(start)
            if stop is not None:
                args.append(stop)
        return self._values.index(*args)

    @scope.register_self
    def __contains__(self, value: Any) -> bool:
        return value in self._values

    @scope.register_self
    def __len__(self) -> int:
        return len(self._values)

    @scope.register_self
    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)

    @overload
    def __getitem__(self, index: int) -> ValueTCov:
        pass

    @overload
    def __getitem__(self, index: slice) -> Self:
        pass

    @scope.register_self
    def __getitem__(self, index: int | slice) -> ValueTCov | Self:
        if isinstance(index, slice):
            return self.__class__(self._values[index])
        return self._values[index]

    @scope.register_self
    def __iter__(self) -> Iterator[ValueTCov]:
        yield from self._values

    @scope.register_self
    def __ne__(self, other: Any) -> bool:
        return super().__ne__(other)

    @scope.register_self
    def __reversed__(self) -> Iterator[ValueTCov]:
        return reversed(self._values)


class ReactiveMutableSequence(MutableSequence[ValueT], ReactiveSequence[ValueT], Generic[ValueT]):
    def append(self, value: ValueT) -> None:
        self._values.append(value)
        self._wire(value)
        self.react.trigger()

    def clear(self) -> None:
        self._unwire(*self._values)
        self._values.clear()
        self.react.trigger()

    def extend(self, other: Iterable[ValueT]) -> None:
        for value in other:
            self._values.append(value)
            self._wire(value)
        self.react.trigger()

    def insert(self, index: int, value: ValueT) -> None:
        self._values.insert(index, value)
        self._wire(value)
        self.react.trigger()

    def pop(self, index: int | None = None) -> ValueT:
        args = () if index is None else (index,)
        value = self._values.pop(*args)
        self._unwire(value)
        self.react.trigger()
        return value

    def remove(self, value: ValueT) -> None:
        self._values.remove(value)
        self._unwire(value)
        self.react.trigger()

    @overload
    def __getitem__(self, index: int) -> ValueT:
        pass

    @overload
    def __getitem__(self, index: slice) -> Self:
        pass

    @scope.register_self
    def __getitem__(self, index: int | slice) -> ValueT | Self:
        if isinstance(index, slice):
            return self.__class__(self._values[index])
        return self._values[index]

    def __delitem__(self, index: int | slice) -> None:
        with suppress(IndexError):
            if isinstance(index, slice):
                self._unwire(*self._values[index])
            else:
                self._unwire(self._values[index])
        del self._values[index]
        self.react.trigger()

    def __iadd__(self, other: Iterable[ValueT]) -> Self:
        for value in other:
            self._values.append(value)
            self._wire(value)
        self.react.trigger()
        return self

    @overload
    def __setitem__(self, index: int, value: ValueT) -> None:
        pass

    @overload
    def __setitem__(self, index: slice, value: Iterable[ValueT]) -> None:
        pass

    def __setitem__(self, index: int | slice, value: ValueT | Iterable[ValueT]) -> None:
        if isinstance(index, slice):
            self._wire(*cast(Iterable[ValueT], value))
            self._values[index] = cast(Iterable[ValueT], value)
        else:
            self._wire(cast(ValueT, value))
            self._values[index] = cast(ValueT, value)
        self.react.trigger()
