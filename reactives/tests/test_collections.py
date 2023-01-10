from __future__ import annotations

import copy
from typing import Union, TYPE_CHECKING, Iterable, Tuple

import dill as pickle

from reactives import Reactive
from reactives.collections import ReactiveMapping, ReactiveMutableMapping, ReactiveSequence, ReactiveMutableSequence
from reactives.reactor import ReactorController
from reactives.tests import assert_scope_empty, assert_reactor_called, assert_in_scope, assert_not_reactor_called

if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem


class _Reactive(Reactive):
    def __init__(self) -> None:
        super().__init__()
        self.react = ReactorController()


class TestReactiveMapping:
    def test___getstate__(self) -> None:
        value = _Reactive()
        sut = ReactiveMapping[str, Reactive](value=value)
        copied_sut = pickle.loads(pickle.dumps(sut))
        copied_value = copied_sut['value']

        # Assert that the copy contains exactly one value which is a copy of the original.
        assert 1 == len(copied_sut)
        assert value != copied_value

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_sut):
            sut.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(sut):
            copied_sut.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_sut):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(sut):
                    with assert_reactor_called(value):
                        value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(sut):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_sut):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test___copy__(self) -> None:
        value = _Reactive()
        sut = ReactiveMapping[str, Reactive](value=value)
        copied_sut = copy.copy(sut)

        # Assert that the copy contains exactly the same values as the original.
        assert 1 == len(copied_sut)
        assert value is copied_sut['value']

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_sut):
            sut.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(sut):
            copied_sut.react.trigger()

        # Assert that triggering the value triggers both the original and the copy.
        with assert_reactor_called(copied_sut):
            with assert_reactor_called(sut):
                value.react.trigger()

    def test___deepcopy__(self) -> None:
        value = _Reactive()
        sut = ReactiveMapping[str, Reactive](value=value)
        copied_sut = copy.deepcopy(sut)
        copied_value = copied_sut['value']

        # Assert that the copy contains exactly one value which is a copy of the original.
        assert 1 == len(copied_sut)
        assert value is not copied_value

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_sut):
            sut.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(sut):
            copied_sut.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_sut):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(sut):
                    value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(sut):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_sut):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test_get(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert 2 == sut.get('two')

    def test_get_with_default(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert 3 == sut.get('three', 3)

    def test_items(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert [('one', 1), ('two', 2)] == list(sut.items())

    def test_keys(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert ['one', 'two'] == list(sut.keys())

    def test_values(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert {'one': 1, 'two': 2} == dict(sut.items())

    def test_contains(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert 'one' in sut
            assert 'three' not in sut

    def test_eq(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert {
                'one': 1,
                'two': 2,
            } == sut

    def test_getitem(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert 2 == sut['two']

    def test_iter(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert ['one', 'two'] == list(iter(sut))

    def test_len(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert 2 == len(sut)

    def test_ne(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert {
                'two': 1,
                'one': 2,
            } != sut

    def test_reversed(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            assert ['two', 'one'] == list(reversed(sut))


class TestReactiveMutableMapping:
    def test_clear(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, int]](one=1, reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.clear()
        assert {} == dict(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive](reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop('reactive')
        assert {} == dict(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_with_default(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive](reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                assert 3 == sut.pop('three', 3)
        assert dict(reactive=reactive_value) == dict(sut)

    def test_popitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive](reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                key, value = sut.popitem()
        assert 'reactive' == key
        assert reactive_value == value
        assert {} == dict(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_setdefault_with_existing_key(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, str]](reactive=reactive_value)
        with assert_in_scope(sut):
            with assert_not_reactor_called(sut):
                assert reactive_value == sut.setdefault('reactive')

    def test_setdefault_with_unknown_key(self) -> None:
        sut = ReactiveMutableMapping[str, Reactive]()
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                assert sut.setdefault('reactive') is None
        assert sut['reactive'] is None

    def test_setdefault_with_existing_key_with_value(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, str]](reactive='notActuallyReactive')
        with assert_in_scope(sut):
            with assert_not_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        assert reactive_value != sut['reactive']
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_setdefault_with_unknown_key_with_value(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive]()
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        assert reactive_value == sut['reactive']
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_update_with_supports_keys_and_get_item(self) -> None:
        reactive_value_1 = _Reactive()
        reactive_value_2 = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, int]](reactive_1=reactive_value_1)
        update_value: SupportsKeysAndGetItem = {
            'reactive_2': reactive_value_2,
            'two': 2,
        }
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.update(update_value)
        assert {
            'reactive_1': reactive_value_1,
            'reactive_2': reactive_value_2,
            'two': 2,
        } == dict(sut)
        with assert_reactor_called(sut):
            reactive_value_1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value_2.react.trigger()

    def test_update_with_iterable(self) -> None:
        reactive_value_1 = _Reactive()
        reactive_value_2 = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, int]](reactive_1=reactive_value_1)
        update_value: Iterable[Tuple[str, Union[Reactive, int]]] = [
            ('reactive_2', reactive_value_2),
            ('two', 2),
        ]
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.update(update_value)
        assert {
            'reactive_1': reactive_value_1,
            'reactive_2': reactive_value_2,
            'two': 2,
        } == dict(sut)
        with assert_reactor_called(sut):
            reactive_value_1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value_2.react.trigger()

    def test_update_with_kwargs(self) -> None:
        reactive_value_1 = _Reactive()
        reactive_value_2 = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, int]](reactive_1=reactive_value_1)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.update(reactive_2=reactive_value_2, two=2)
        assert {
            'reactive_1': reactive_value_1,
            'reactive_2': reactive_value_2,
            'two': 2,
        } == dict(sut)
        with assert_reactor_called(sut):
            reactive_value_1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value_2.react.trigger()

    def test_delitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive](reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut['reactive']
        assert {} == dict(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_setitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive]()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut['reactive'] = reactive_value
        assert reactive_value == sut['reactive']
        with assert_reactor_called(sut):
            reactive_value.react.trigger()


class TestReactiveSequence:
    def test___getstate__(self) -> None:
        value = _Reactive()
        sut = ReactiveSequence[Reactive]([value])
        copied_sut = pickle.loads(pickle.dumps(sut))
        copied_value = copied_sut[0]

        # Assert that the copy contains exactly one value which is a copy of the original.
        assert 1 == len(copied_sut)
        assert value is not copied_value

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_sut):
            sut.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(sut):
            copied_sut.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_sut):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(sut):
                    with assert_reactor_called(value):
                        value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(sut):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_sut):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test___copy__(self) -> None:
        value = _Reactive()
        sut = ReactiveSequence[Reactive]([value])
        copied_sut = copy.copy(sut)

        # Assert that the copy contains exactly the same values as the original.
        assert 1 == len(copied_sut)
        assert value is copied_sut[0]

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_sut):
            sut.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(sut):
            copied_sut.react.trigger()

        # Assert that triggering the value triggers both the original and the copy.
        with assert_reactor_called(value):
            with assert_reactor_called(copied_sut):
                value.react.trigger()

    def test___deepcopy__(self) -> None:
        value = _Reactive()
        sut = ReactiveSequence[Reactive]([value])
        copied_sut = copy.deepcopy(sut)
        copied_value = copied_sut[0]

        # Assert that the copy contains exactly one value which is a copy of the original.
        assert 1 == len(copied_sut)
        assert value is not copied_value

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_sut):
            sut.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(sut):
            copied_sut.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_sut):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(sut):
                    with assert_reactor_called(value):
                        value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(sut):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_sut):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test_count(self) -> None:
        sut = ReactiveSequence[int]([1, 2, 1])
        with assert_in_scope(sut):
            assert 2 == sut.count(1)

    def test_index_without_slice(self) -> None:
        sut = ReactiveSequence[int]([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            assert 1 == sut.index(2)

    def test_index_with_slice(self) -> None:
        sut = ReactiveSequence[int]([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            assert 2 == sut.index(1, 2, 5)

    def test_contains(self) -> None:
        sut = ReactiveSequence[int]([1])
        with assert_in_scope(sut):
            assert 1 in sut
            assert 2 not in sut

    def test___getitem_with_int(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert 2 == sut[1]

    def test___getitem_with_slice(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert [1, 2] == list(sut[0:2])

    def test_iter(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert [1, 2] == list(iter(sut))

    def test_len(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert 2 == len(sut)

    def test_ne(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert [2, 1] != list(sut)

    def test_reversed(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert [2, 1] == list(reversed(sut))


class TestReactiveMutableSequence:
    def test_append(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Reactive]()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.append(reactive_value)
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_clear(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Reactive]([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.clear()
        assert [] == list(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_extend(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.extend([reactive_value1, reactive_value2])
        assert [1, 2, reactive_value1, reactive_value2] == list(sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_insert(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.insert(1, reactive_value)
        assert [1, reactive_value, 2] == list(sut)
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_without_index(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, 2, reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop()
        assert [1, 2] == list(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_with_index(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, reactive_value, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop(1)
        assert [1, 2] == list(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_remove(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Reactive]([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.remove(reactive_value)
        assert [] == list(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_delitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Reactive]([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[0]
        assert [] == list(sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_iadd(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut += [reactive_value1, reactive_value2]
        assert [1, 2, reactive_value1, reactive_value2] == list(sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test___setitem__with_int(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut[0] = reactive_value
        assert reactive_value == sut[0]
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test___setitem__with_slice(self) -> None:
        reactive_value_1 = _Reactive()
        reactive_value_2 = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut[0:2] = reactive_value_1, reactive_value_2
        assert [reactive_value_1, reactive_value_2] == list(sut[0:2])
        with assert_reactor_called(sut):
            reactive_value_1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value_2.react.trigger()

    def test___getitem__with_int(self) -> None:
        sut = ReactiveMutableSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert 2 == sut[1]

    def test___getitem__with_slice(self) -> None:
        sut = ReactiveMutableSequence[int]([1, 2])
        with assert_in_scope(sut):
            assert [1, 2] == list(sut[0:2])
