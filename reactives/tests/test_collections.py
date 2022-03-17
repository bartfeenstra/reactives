import copy
import dill as pickle
import sys
import unittest
from unittest import TestCase

from reactives import reactive
from reactives.collections import ReactiveList, ReactiveDict
from reactives.factory.type import ReactiveInstance
from reactives.tests import assert_scope_empty, assert_reactor_called, assert_in_scope, assert_not_reactor_called


@reactive
class _Reactive(ReactiveInstance):
    pass


class ReactiveDictTest(TestCase):
    def test___getstate__(self) -> None:
        value = _Reactive()
        subject = ReactiveDict(value=value)
        copied_subject = pickle.loads(pickle.dumps(subject))
        copied_value = copied_subject['value']

        # Assert that the copy contains exactly one value which is a copy of the original.
        self.assertEqual(1, len(copied_subject))
        self.assertIsNot(value, copied_value)

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_subject):
            subject.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(subject):
            copied_subject.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_subject):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(subject):
                    with assert_reactor_called(value):
                        value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(subject):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_subject):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test___copy__(self) -> None:
        value = _Reactive()
        subject = ReactiveDict(value=value)
        copied_subject = copy.copy(subject)

        # Assert that the copy contains exactly the same values as the original.
        self.assertEqual(1, len(copied_subject))
        self.assertIs(value, copied_subject['value'])

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_subject):
            subject.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(subject):
            copied_subject.react.trigger()

        # Assert that triggering the value triggers both the original and the copy.
        with assert_reactor_called(value):
            with assert_reactor_called(copied_subject):
                value.react.trigger()

    def test___deepcopy__(self) -> None:
        value = _Reactive()
        subject = ReactiveDict(value=value)
        copied_subject = copy.deepcopy(subject)
        copied_value = copied_subject['value']

        # Assert that the copy contains exactly one value which is a copy of the original.
        self.assertEqual(1, len(copied_subject))
        self.assertIsNot(value, copied_value)

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_subject):
            subject.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(subject):
            copied_subject.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_subject):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(subject):
                    with assert_reactor_called(value):
                        value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(subject):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_subject):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test_clear(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveDict(one=1, reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.clear()
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_get(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(2, sut.get('two'))

    def test_items(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual([('one', 1), ('two', 2)], list(sut.items()))

    def test_keys(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(['one', 'two'], list(sut.keys()))

    def test_pop(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop('reactive')
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_popitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                key, value = sut.popitem()
        self.assertEqual('reactive', key)
        self.assertEqual(reactive_value, value)
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_setdefault_with_existing_key(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveDict(reactive='notActuallyReactive')
        with assert_in_scope(sut):
            with assert_not_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertNotEqual(reactive_value, dict.get(sut, 'reactive'))
        self.assertNotIn(sut, reactive_value.react._reactors)

    def test_setdefault_with_unknown_key(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveDict()
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertEqual(reactive_value, dict.get(sut, 'reactive'))
        self.assertIn(sut, reactive_value.react._reactors)

    def test_update(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveDict(one=1)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.update({
                    'reactive': reactive_value
                })
        self.assertEqual(reactive_value, dict.get(sut, 'reactive'))
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
        reactive_value = _Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut['reactive']
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_eq(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual({
                'one': 1,
                'two': 2,
            }, sut)

    def test_getitem(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(2, sut['two'])

    def test_iter(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertCountEqual(['one', 'two'], iter(sut))

    def test_len(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertEqual(2, len(sut))

    def test_ne(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            self.assertNotEqual({
                'two': 1,
                'one': 2,
            }, sut)

    @unittest.skipIf(not hasattr(dict, '__reversed__'), 'Dictionary reversal is available in Python 3.8 and later only.')
    def test_reversed(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            # Because dictionary order isn't guaranteed before Python 3.7, we cannot compare to a hardcoded list of
            # expected keys.
            self.assertEqual(['two', 'one'], list(reversed(sut)))

    def test_setitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveDict()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut['reactive'] = reactive_value
        self.assertEqual(reactive_value, sut['reactive'])
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_sizeof(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with assert_in_scope(sut):
            sys.getsizeof(sut)


class ReactiveListTest(TestCase):
    def test___getstate__(self) -> None:
        value = _Reactive()
        subject = ReactiveList([value])
        copied_subject = pickle.loads(pickle.dumps(subject))
        copied_value = copied_subject[0]

        # Assert that the copy contains exactly one value which is a copy of the original.
        self.assertEqual(1, len(copied_subject))
        self.assertIsNot(value, copied_value)

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_subject):
            subject.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(subject):
            copied_subject.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_subject):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(subject):
                    with assert_reactor_called(value):
                        value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(subject):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_subject):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test___copy__(self) -> None:
        value = _Reactive()
        subject = ReactiveList([value])
        copied_subject = copy.copy(subject)

        # Assert that the copy contains exactly the same values as the original.
        self.assertEqual(1, len(copied_subject))
        self.assertIs(value, copied_subject[0])

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_subject):
            subject.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(subject):
            copied_subject.react.trigger()

        # Assert that triggering the value triggers both the original and the copy.
        with assert_reactor_called(value):
            with assert_reactor_called(copied_subject):
                value.react.trigger()

    def test_copy(self) -> None:
        value = _Reactive()
        subject = ReactiveList([value])
        copied_subject = subject.copy()

        # Assert that the copy contains exactly the same values as the original.
        self.assertEqual(1, len(copied_subject))
        self.assertIs(value, copied_subject[0])

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_subject):
            subject.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(subject):
            copied_subject.react.trigger()

        # Assert that triggering the value triggers both the original and the copy.
        with assert_reactor_called(value):
            with assert_reactor_called(copied_subject):
                value.react.trigger()

    def test___deepcopy__(self) -> None:
        value = _Reactive()
        subject = ReactiveList([value])
        copied_subject = copy.deepcopy(subject)
        copied_value = copied_subject[0]

        # Assert that the copy contains exactly one value which is a copy of the original.
        self.assertEqual(1, len(copied_subject))
        self.assertIsNot(value, copied_value)

        # Assert that triggering the original does not trigger the copy.
        with assert_not_reactor_called(copied_subject):
            subject.react.trigger()

        # Assert that triggering the copy does not trigger the original.
        with assert_not_reactor_called(subject):
            copied_subject.react.trigger()

        # Assert that neither the copied instance nor the copied value is triggered when triggering the original value.
        with assert_not_reactor_called(copied_subject):
            with assert_not_reactor_called(copied_value):
                with assert_reactor_called(subject):
                    with assert_reactor_called(value):
                        value.react.trigger()

        # Assert that neither the original instance nor the original value is triggered when triggering the copied
        # value.
        with assert_not_reactor_called(subject):
            with assert_not_reactor_called(value):
                with assert_reactor_called(copied_subject):
                    with assert_reactor_called(copied_value):
                        copied_value.react.trigger()

    def test_append(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList()
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.append(reactive_value)
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_clear(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.clear()
        self.assertEqual([], sut)
        self.assertEqual([], reactive_value.react._reactors)

    def test_count(self) -> None:
        sut = ReactiveList([1, 2, 1])
        with assert_in_scope(sut):
            self.assertEqual(2, sut.count(1))

    def test_extend(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveList([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.extend([reactive_value1, reactive_value2])
        self.assertEqual([1, 2, reactive_value1, reactive_value2], sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_index_without_slice(self) -> None:
        sut = ReactiveList([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            self.assertEqual(1, sut.index(2))

    def test_index_with_slice(self) -> None:
        sut = ReactiveList([1, 2, 1, 2, 1, 2, 1, 2])
        with assert_in_scope(sut):
            self.assertEqual(2, sut.index(1, 2, 5))

    def test_insert(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.insert(1, reactive_value)
        self.assertEqual([1, reactive_value, 2], sut)
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_without_index(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([1, 2, reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop()
        self.assertEqual([1, 2], sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_with_index(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([1, reactive_value, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.pop(1)
        self.assertEqual([1, 2], sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_remove(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.remove(reactive_value)
        self.assertEqual([], sut)
        with assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_reverse(self) -> None:
        sut = ReactiveList([1, 2, 3])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.reverse()
        self.assertEqual([3, 2, 1], sut)

    def test_sort(self) -> None:
        sut = ReactiveList([3, 2, 1])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.sort()
        self.assertEqual([1, 2, 3], sut)

    def test_sort_with_key(self) -> None:
        sut = ReactiveList(['xc', 'yb', 'za'])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.sort(key=lambda x: x[1])
        self.assertEqual(['za', 'yb', 'xc'], sut)

    def test_sort_with_reversed(self) -> None:
        sut = ReactiveList([1, 2, 3])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.sort(reverse=True)
        self.assertEqual([3, 2, 1], sut)

    def test_add(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([reactive_value])
        other = [1, 2]
        with assert_scope_empty():
            with assert_not_reactor_called(sut):
                new_sut = sut + other
        self.assertEqual([reactive_value, 1, 2], new_sut)
        with assert_reactor_called(new_sut):
            reactive_value.react.trigger()

    def test_contains(self) -> None:
        sut = ReactiveList([1])
        with assert_in_scope(sut):
            self.assertIn(1, sut)
            self.assertNotIn(2, sut)

    def test_delitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([reactive_value])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[0]
        self.assertEqual([], sut)
        self.assertEqual([], reactive_value.react._reactors)

    def test_eq(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEqual([1, 2], sut)

    def test_getitem(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEqual(2, sut[1])

    def test_iadd(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut += [reactive_value1, reactive_value2]
        self.assertEqual([1, 2, reactive_value1, reactive_value2], sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_imul(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with assert_in_scope(sut):
            with assert_reactor_called(sut):
                sut *= 2
        self.assertEqual([reactive_value1, reactive_value2, reactive_value1, reactive_value2], sut)
        with assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_iter(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEqual([1, 2], list(iter(sut)))

    def test_len(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEqual(2, len(sut))

    def test_mul(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with assert_scope_empty():
            with assert_not_reactor_called(sut):
                new_sut = sut * 2
        self.assertEqual([reactive_value1, reactive_value2, reactive_value1, reactive_value2], new_sut)
        with assert_reactor_called(new_sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(new_sut):
            reactive_value2.react.trigger()

    def test_ne(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertNotEqual([2, 1], sut)

    def test_reversed(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            self.assertEqual([2, 1], list(reversed(sut)))

    def test_rmul(self) -> None:
        reactive_value1 = _Reactive()
        reactive_value2 = _Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with assert_scope_empty():
            with assert_not_reactor_called(sut):
                new_sut = 2 * sut
        self.assertEqual([reactive_value1, reactive_value2, reactive_value1, reactive_value2], new_sut)
        with assert_reactor_called(new_sut):
            reactive_value1.react.trigger()
        with assert_reactor_called(new_sut):
            reactive_value2.react.trigger()

    def test_setitem(self) -> None:
        reactive_value = _Reactive()
        sut = ReactiveList([1, 2])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut[1] = reactive_value
        self.assertEqual(reactive_value, sut[1])
        with assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_sizeof(self) -> None:
        sut = ReactiveList([1, 2])
        with assert_in_scope(sut):
            sys.getsizeof(sut)
