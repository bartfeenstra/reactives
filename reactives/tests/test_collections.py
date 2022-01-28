import sys
import unittest
from unittest import TestCase

from reactives import reactive
from reactives.collections import ReactiveList, ReactiveDict
from reactives.tests import assert_scope_empty, assert_reactor_called, assert_in_scope, assert_not_reactor_called


class ReactiveDictTest(TestCase):
    @reactive
    class Reactive:
        pass

    def test_clear(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(one=1, reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.clear()
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_get(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEquals(2, sut.get('two'))

    def test_items(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEquals([('one', 1), ('two', 2)], list(sut.items()))

    def test_keys(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEquals(['one', 'two'], list(sut.keys()))

    def test_pop(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop('reactive')
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_popitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                key, value = sut.popitem()
        self.assertEquals('reactive', key)
        self.assertEquals(reactive_value, value)
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_setdefault_with_existing_key(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive='notActuallyReactive')
        with assert_in_scope(sut):
            with assert_not_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertNotEquals(reactive_value, dict.get(sut, 'reactive'))
        self.assertNotIn(sut, reactive_value.react._reactors)

    def test_setdefault_with_unknown_key(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict()
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertEquals(reactive_value, dict.get(sut, 'reactive'))
        self.assertIn(sut, reactive_value.react._reactors)

    def test_update(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(one=1)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.update({
                    'reactive': reactive_value
                })
        self.assertEquals(reactive_value, dict.get(sut, 'reactive'))
        self.assertIn(sut, reactive_value.react._reactors)

    def test_values(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertCountEqual([1, 2], list(sut.values()))

    def test_contains(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertIn('one', sut)
            self.assertNotIn('three', sut)

    def test_delitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut['reactive']
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_eq(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEquals({
                'one': 1,
                'two': 2,
            }, sut)

    def test_getitem(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEquals(2, sut['two'])

    def test_iter(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertCountEqual(['one', 'two'], iter(sut))

    def test_len(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEquals(2, len(sut))

    def test_ne(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertNotEquals({
                'two': 1,
                'one': 2,
            }, sut)

    @unittest.skipIf(not hasattr(dict, '__reversed__'), 'Dictionary reversal is available in Python 3.8 and later only.')
    def test_reversed(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            # Because dictionary order isn't guaranteed before Python 3.7, we cannot compare to a hardcoded list of
            # expected keys.
            self.assertEquals(['two', 'one'], list(reversed(sut)))

    def test_setitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut['reactive'] = reactive_value
        self.assertEquals(reactive_value, sut['reactive'])
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_sizeof(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            sys.getsizeof(sut)


class ReactiveListTest(TestCase):
    @reactive
    class Reactive:
        pass

    def test_append(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.append(reactive_value)
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_clear(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.clear()
        self.assertEquals([], sut)
        self.assertEquals([], reactive_value.react._reactors)

    def test_copy(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEquals([1, 2], sut.copy())

    def test_count(self) -> None:
        sut = ReactiveList([1, 2, 1])
        with assert_in_scope(sut):
            self.assertEquals(2, sut.count(1))

    def test_extend(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.extend([reactive_value1, reactive_value2])
        self.assertEquals([1, 2, reactive_value1, reactive_value2], sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_index_without_slice(self) -> None:
        sut = ReactiveList([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            self.assertEquals(1, sut.index(2))

    def test_index_with_slice(self) -> None:
        sut = ReactiveList([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            self.assertEquals(2, sut.index(1, 2, 5))

    def test_insert(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.insert(1, reactive_value)
        self.assertEquals([1, reactive_value, 2], sut)
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_without_index(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, 2, reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop()
        self.assertEquals([1, 2], sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_with_index(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, reactive_value, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop(1)
        self.assertEquals([1, 2], sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_remove(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.remove(reactive_value)
        self.assertEquals([], sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_reverse(self) -> None:
        sut = ReactiveList([1, 2, 3])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.reverse()
        self.assertEquals([3, 2, 1], sut)

    def test_sort(self) -> None:
        sut = ReactiveList([3, 2, 1])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.sort()
        self.assertEquals([1, 2, 3], sut)

    def test_sort_with_key(self) -> None:
        sut = ReactiveList(['xc', 'yb', 'za'])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.sort(key=lambda x: x[1])
        self.assertEquals(['za', 'yb', 'xc'], sut)

    def test_sort_with_reversed(self) -> None:
        sut = ReactiveList([1, 2, 3])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.sort(reverse=True)
        self.assertEquals([3, 2, 1], sut)

    def test_add(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([reactive_value])
        other = [1, 2]
        with assert_scope_empty():
            with assert_not_reactor_called(sut):
                new_sut = sut + other
        self.assertEquals([reactive_value, 1, 2], new_sut)
        with assert_reactor_called(new_sut):
            reactive_value.react.trigger()

    def test_contains(self) -> None:
        sut = ReactiveList([1])
        with assert_in_scope(sut):
            self.assertIn(1, sut)
            self.assertNotIn(2, sut)

    def test_delitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[0]
        self.assertEquals([], sut)
        self.assertEquals([], reactive_value.react._reactors)

    def test_eq(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEquals([1, 2], sut)

    def test_getitem(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEquals(2, sut[1])

    def test_iadd(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut += [reactive_value1, reactive_value2]
        self.assertEquals([1, 2, reactive_value1, reactive_value2], sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_imul(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut *= 2
        self.assertEquals([reactive_value1, reactive_value2,
                           reactive_value1, reactive_value2], sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_iter(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEquals([1, 2], list(iter(sut)))

    def test_len(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEquals(2, len(sut))

    def test_mul(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with assert_scope_empty():
            with assert_not_reactor_called(sut):
                new_sut = sut * 2
        self.assertEquals([reactive_value1, reactive_value2,
                           reactive_value1, reactive_value2], new_sut)
        with assert_reactor_called(new_sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(new_sut):
            reactive_value2.react.trigger()

    def test_ne(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertNotEquals([2, 1], sut)

    def test_reversed(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEquals([2, 1], list(reversed(sut)))

    def test_rmul(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with assert_scope_empty():
            with assert_not_reactor_called(sut):
                new_sut = 2 * sut
        self.assertEquals([reactive_value1, reactive_value2,
                           reactive_value1, reactive_value2], new_sut)
        with assert_reactor_called(new_sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(new_sut):
            reactive_value2.react.trigger()

    def test_setitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut[1] = reactive_value
        self.assertEquals(reactive_value, sut[1])
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_sizeof(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            sys.getsizeof(sut)
