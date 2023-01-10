from __future__ import annotations

import copy
from typing import Union, TYPE_CHECKING, Iterable, Tuple
from unittest import TestCase

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


class ReactiveMappingTest(TestCase):
    def test___getstate__(self) -> None:
        value = _Reactive()
        sut = ReactiveMapping[str, Reactive](value=value)
        copied_sut = pickle.loads(pickle.dumps(sut))
        copied_value = copied_sut['value']

        # Assert that the copy contains exactly one value which is a copy of the original.
        self.assertEqual(1, len(copied_sut))
        self.assertIsNot(value, copied_value)

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
        self.assertEqual(1, len(copied_sut))
        self.assertIs(value, copied_sut['value'])

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
        self.assertEqual(1, len(copied_sut))
        self.assertIsNot(value, copied_value)

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
            self.assertEqual(2, sut.get('two'))

    def test_get_with_default(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(3, sut.get('three', 3))

    def test_items(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual([('one', 1), ('two', 2)], list(sut.items()))

    def test_keys(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(['one', 'two'], list(sut.keys()))

    def test_values(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual({'one': 1, 'two': 2}, dict(sut.items()))

    def test_contains(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertIn('one', sut)
            self.assertNotIn('three', sut)

    def test_eq(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual({
                'one': 1,
                'two': 2,
            }, sut)

    def test_getitem(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(2, sut['two'])

    def test_iter(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertCountEqual(['one', 'two'], iter(sut))

    def test_len(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(2, len(sut))

    def test_ne(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertNotEqual({
                'two': 1,
                'one': 2,
            }, sut)

    def test_reversed(self) -> None:
        sut = ReactiveMapping[str, int](one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(['two', 'one'], list(reversed(sut)))


class ReactiveMutableMappingTest(TestCase):
    def test_clear(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, int]](one=1, reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.clear()
        self.assertCountEqual({}, dict(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive](reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop('reactive')
        self.assertEqual({}, dict(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_with_default(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive](reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                self.assertEqual(3, sut.pop('three', 3))
        self.assertEqual(dict(reactive=reactive_value), dict(sut))

    def test_popitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive](reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                key, value = sut.popitem()
        self.assertEqual('reactive', key)
        self.assertEqual(reactive_value, value)
        self.assertEqual({}, dict(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_setdefault_with_existing_key(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, str]](reactive=reactive_value)
        with assert_in_scope(sut):
            with assert_not_reactor_called(sut):
                self.assertEqual(reactive_value, sut.setdefault('reactive'))

    def test_setdefault_with_unknown_key(self) -> None:
        sut = ReactiveMutableMapping[str, Reactive]()
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                self.assertIsNone(sut.setdefault('reactive'))
        self.assertIsNone(sut['reactive'])

    def test_setdefault_with_existing_key_with_value(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Union[Reactive, str]](reactive='notActuallyReactive')
        with assert_in_scope(sut):
            with assert_not_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertNotEqual(reactive_value, sut['reactive'])
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_setdefault_with_unknown_key_with_value(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive]()
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertEqual(reactive_value, sut['reactive'])
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
        self.assertEqual({
            'reactive_1': reactive_value_1,
            'reactive_2': reactive_value_2,
            'two': 2,
        }, dict(sut))
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
        self.assertEqual({
            'reactive_1': reactive_value_1,
            'reactive_2': reactive_value_2,
            'two': 2,
        }, dict(sut))
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
        self.assertEqual({
            'reactive_1': reactive_value_1,
            'reactive_2': reactive_value_2,
            'two': 2,
        }, dict(sut))
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
        self.assertEqual({}, dict(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_setitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableMapping[str, Reactive]()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut['reactive'] = reactive_value
        self.assertEqual(reactive_value, sut['reactive'])
        with assert_reactor_called(sut):
            reactive_value.react.trigger()


class ReactiveSequenceTest(TestCase):
    def test___getstate__(self) -> None:
        value = _Reactive()
        sut = ReactiveSequence[Reactive]([value])
        copied_sut = pickle.loads(pickle.dumps(sut))
        copied_value = copied_sut[0]

        # Assert that the copy contains exactly one value which is a copy of the original.
        self.assertEqual(1, len(copied_sut))
        self.assertIsNot(value, copied_value)

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
        self.assertEqual(1, len(copied_sut))
        self.assertIs(value, copied_sut[0])

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
        self.assertEqual(1, len(copied_sut))
        self.assertIsNot(value, copied_value)

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
            self.assertEqual(2, sut.count(1))

    def test_index_without_slice(self) -> None:
        sut = ReactiveSequence[int]([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            self.assertEqual(1, sut.index(2))

    def test_index_with_slice(self) -> None:
        sut = ReactiveSequence[int]([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            self.assertEqual(2, sut.index(1, 2, 5))

    def test_contains(self) -> None:
        sut = ReactiveSequence[int]([1])
        with assert_in_scope(sut):
            self.assertIn(1, sut)
            self.assertNotIn(2, sut)

    def test___getitem_with_int(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertEqual(2, sut[1])

    def test___getitem_with_slice(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertEqual([1, 2], list(sut[0:2]))

    def test_iter(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertEqual([1, 2], list(iter(sut)))

    def test_len(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertEqual(2, len(sut))

    def test_ne(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertNotEqual([2, 1], list(sut))

    def test_reversed(self) -> None:
        sut = ReactiveSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertEqual([2, 1], list(reversed(sut)))


class ReactiveMutableSequenceTest(TestCase):
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
        self.assertEqual([], list(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_extend(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.extend([reactive_value1, reactive_value2])
        self.assertEqual([1, 2, reactive_value1, reactive_value2], list(sut))
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
        self.assertEqual([1, reactive_value, 2], list(sut))
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_without_index(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, 2, reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop()
        self.assertEqual([1, 2], list(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_with_index(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, reactive_value, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop(1)
        self.assertEqual([1, 2], list(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_remove(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Reactive]([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.remove(reactive_value)
        self.assertEqual([], list(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_delitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveMutableSequence[Reactive]([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[0]
        self.assertEqual([], list(sut))
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_iadd(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut += [reactive_value1, reactive_value2]
        self.assertEqual([1, 2, reactive_value1, reactive_value2], list(sut))
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
        self.assertEqual(reactive_value, sut[0])
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test___setitem__with_slice(self) -> None:
        reactive_value_1 = _Reactive()
        reactive_value_2 = _Reactive()
        sut = ReactiveMutableSequence[Union[Reactive, int]]([1])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut[0:2] = reactive_value_1, reactive_value_2
        self.assertEqual([reactive_value_1, reactive_value_2], list(sut[0:2]))
        with assert_reactor_called(sut):
            reactive_value_1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value_2.react.trigger()

    def test___getitem__with_int(self) -> None:
        sut = ReactiveMutableSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertEqual(2, sut[1])

    def test___getitem__with_slice(self) -> None:
        sut = ReactiveMutableSequence[int]([1, 2])
        with assert_in_scope(sut):
            self.assertEqual([1, 2], list(sut[0:2]))
