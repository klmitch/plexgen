import unittest

import mock

from plexgen import prioq


class TestKeyWrap(unittest.TestCase):
    truth_tab = [
        (
            'test_eq_equal',
            '__eq__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('obj2', key),
            True,
            [mock.call('obj1'), mock.call('obj2')],
        ),
        (
            'test_eq_not_equal',
            '__eq__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('ojb2', key),
            False,
            [mock.call('obj1'), mock.call('ojb2')],
        ),
        (
            'test_eq_equal_unwrapped',
            '__eq__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 'obj',
            True,
            [mock.call('obj1')],
        ),
        (
            'test_eq_not_equal_unwrapped',
            '__eq__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 'ojb',
            False,
            [mock.call('obj1')],
        ),

        (
            'test_ne_equal',
            '__ne__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('obj2', key),
            False,
            [mock.call('obj1'), mock.call('obj2')],
        ),
        (
            'test_ne_not_equal',
            '__ne__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('ojb2', key),
            True,
            [mock.call('obj1'), mock.call('ojb2')],
        ),
        (
            'test_ne_equal_unwrapped',
            '__ne__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 'obj',
            False,
            [mock.call('obj1')],
        ),
        (
            'test_ne_not_equal_unwrapped',
            '__ne__',
            lambda x: x[:-1],
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 'ojb',
            True,
            [mock.call('obj1')],
        ),

        (
            'test_lt_less',
            '__lt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('obj2', key),
            True,
            [mock.call('obj1'), mock.call('obj2')],
        ),
        (
            'test_lt_equal',
            '__lt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: prioq.KeyWrap('obj2', key),
            False,
            [mock.call('object2'), mock.call('obj2')],
        ),
        (
            'test_lt_greater',
            '__lt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: prioq.KeyWrap('obj1', key),
            False,
            [mock.call('obj2'), mock.call('obj1')],
        ),
        (
            'test_lt_less_unwrapped',
            '__lt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 2,
            True,
            [mock.call('obj1')],
        ),
        (
            'test_lt_equal_unwrapped',
            '__lt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: 2,
            False,
            [mock.call('object2')],
        ),
        (
            'test_lt_greater',
            '__lt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: 1,
            False,
            [mock.call('obj2')],
        ),


        (
            'test_le_less',
            '__le__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('obj2', key),
            True,
            [mock.call('obj1'), mock.call('obj2')],
        ),
        (
            'test_le_equal',
            '__le__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: prioq.KeyWrap('obj2', key),
            True,
            [mock.call('object2'), mock.call('obj2')],
        ),
        (
            'test_le_greater',
            '__le__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: prioq.KeyWrap('obj1', key),
            False,
            [mock.call('obj2'), mock.call('obj1')],
        ),
        (
            'test_le_less_unwrapped',
            '__le__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 2,
            True,
            [mock.call('obj1')],
        ),
        (
            'test_le_equal_unwrapped',
            '__le__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: 2,
            True,
            [mock.call('object2')],
        ),
        (
            'test_le_greater',
            '__le__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: 1,
            False,
            [mock.call('obj2')],
        ),

        (
            'test_gt_less',
            '__gt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('obj2', key),
            False,
            [mock.call('obj1'), mock.call('obj2')],
        ),
        (
            'test_gt_equal',
            '__gt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: prioq.KeyWrap('obj2', key),
            False,
            [mock.call('object2'), mock.call('obj2')],
        ),
        (
            'test_gt_greater',
            '__gt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: prioq.KeyWrap('obj1', key),
            True,
            [mock.call('obj2'), mock.call('obj1')],
        ),
        (
            'test_gt_less_unwrapped',
            '__gt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 2,
            False,
            [mock.call('obj1')],
        ),
        (
            'test_gt_equal_unwrapped',
            '__gt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: 2,
            False,
            [mock.call('object2')],
        ),
        (
            'test_gt_greater',
            '__gt__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: 1,
            True,
            [mock.call('obj2')],
        ),


        (
            'test_ge_less',
            '__ge__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: prioq.KeyWrap('obj2', key),
            False,
            [mock.call('obj1'), mock.call('obj2')],
        ),
        (
            'test_ge_equal',
            '__ge__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: prioq.KeyWrap('obj2', key),
            True,
            [mock.call('object2'), mock.call('obj2')],
        ),
        (
            'test_ge_greater',
            '__ge__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: prioq.KeyWrap('obj1', key),
            True,
            [mock.call('obj2'), mock.call('obj1')],
        ),
        (
            'test_ge_less_unwrapped',
            '__ge__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj1', key),
            lambda key: 2,
            False,
            [mock.call('obj1')],
        ),
        (
            'test_ge_equal_unwrapped',
            '__ge__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('object2', key),
            lambda key: 2,
            True,
            [mock.call('object2')],
        ),
        (
            'test_ge_greater',
            '__ge__',
            lambda x: int(x[-1]),
            lambda key: prioq.KeyWrap('obj2', key),
            lambda key: 1,
            True,
            [mock.call('obj2')],
        ),
    ]

    def test_init(self):
        result = prioq.KeyWrap('obj', 'key')

        self.assertEqual(result.obj, 'obj')
        self.assertEqual(result.key, 'key')

    def test_truth_tab(self):
        for test, func, key, obj1, obj2, expect, calls in self.truth_tab:
            key = mock.Mock(side_effect=key)
            obj1 = obj1(key)
            obj2 = obj2(key)

            result = getattr(obj1, func)(obj2)

            self.assertIs(result, expect,
                          '%s: expected %r, got %r' % (test, expect, result))
            try:
                key.assert_has_calls(calls, any_order=True)
            except AssertionError as e:
                self.fail('%s: %s' % (test, e))
            self.assertEqual(key.call_count, len(calls),
                             '%s: expected %d calls, got %d' %
                             (test, len(calls), key.call_count))


class TestPrioQ(unittest.TestCase):
    @mock.patch.object(prioq.heapq, 'heapify')
    @mock.patch.object(prioq, 'KeyWrap', side_effect=lambda i, k: '%s_w' % i)
    def test_init_base(self, mock_KeyWrap, mock_heapify):
        result = prioq.PrioQ()

        self.assertEqual(result.items, [])
        self.assertEqual(result.key('spam'), 'spam')
        self.assertFalse(mock_KeyWrap.called)
        mock_heapify.assert_called_once_with(result.items)

    @mock.patch.object(prioq.heapq, 'heapify')
    @mock.patch.object(prioq, 'KeyWrap', side_effect=lambda i, k: '%s_w' % i)
    def test_init_alt(self, mock_KeyWrap, mock_heapify):
        result = prioq.PrioQ(['i1', 'i2', 'i3'], 'key')

        self.assertEqual(result.items, ['i1_w', 'i2_w', 'i3_w'])
        self.assertEqual(result.key, 'key')
        mock_KeyWrap.assert_has_calls([
            mock.call('i1', 'key'),
            mock.call('i2', 'key'),
            mock.call('i3', 'key'),
        ])
        self.assertEqual(mock_KeyWrap.call_count, 3)
        mock_heapify.assert_called_once_with(result.items)

    def get_obj(self, items=None, key='key'):
        with mock.patch.object(prioq, 'KeyWrap', side_effect=lambda i, k: i), \
             mock.patch.object(prioq.heapq, 'heapify'):
            return prioq.PrioQ(items, key)

    def test_bool_empty(self):
        obj = self.get_obj()

        self.assertFalse(obj)

    def test_bool_nonempty(self):
        obj = self.get_obj([1, 2, 3])

        self.assertTrue(obj)

    @mock.patch.object(prioq.heapq, 'heappush',
                       side_effect=lambda l, i: l.append(i))
    def test_push(self, mock_heappush):
        obj = self.get_obj([1, 2, 3])

        with mock.patch.object(
                prioq, 'KeyWrap',
                side_effect=lambda i, k: '%s_w' % i,
        ) as mock_KeyWrap:
            obj.push(4, 5, 6)

        self.assertEqual(obj.items, [1, 2, 3, '4_w', '5_w', '6_w'])
        mock_KeyWrap.assert_has_calls([
            mock.call(4, 'key'),
            mock.call(5, 'key'),
            mock.call(6, 'key'),
        ])
        self.assertEqual(mock_KeyWrap.call_count, 3)
        mock_heappush.assert_has_calls([
            mock.call(obj.items, '4_w'),
            mock.call(obj.items, '5_w'),
            mock.call(obj.items, '6_w'),
        ])
        self.assertEqual(mock_heappush.call_count, 3)

    @mock.patch.object(prioq.heapq, 'heappop',
                       side_effect=lambda l: l.pop(0))
    def test_pop(self, mock_heappop):
        items = [
            mock.Mock(obj=1),
            mock.Mock(obj=2),
            mock.Mock(obj=3),
        ]
        obj = self.get_obj(items[:])

        result = obj.pop()

        self.assertEqual(result, 1)
        self.assertEqual(obj.items, items[1:])
        mock_heappop.assert_called_once_with(obj.items)

    def test_top(self):
        items = [
            mock.Mock(obj=1),
            mock.Mock(obj=2),
            mock.Mock(obj=3),
        ]
        obj = self.get_obj(list(items))

        self.assertEqual(obj.top, 1)
        self.assertEqual(obj.items, items)
