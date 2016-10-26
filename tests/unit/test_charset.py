import unittest

import mock
import six

from plexgen import charset


class TestVChars(unittest.TestCase):
    def test_acceptable(self):
        # Ensure no exception is raised
        charset._vchars(97, 98, 99)

    def test_too_low(self):
        self.assertRaises(ValueError, charset._vchars, -1)

    def test_too_high(self):
        self.assertRaises(ValueError, charset._vchars, charset.MAX_CHAR + 1)


class TestQChar(unittest.TestCase):
    def test_graph(self):
        for i in range(charset.MIN_GRAPH, charset.MAX_GRAPH + 1):
            result = charset._qchar(i)

            if i in charset.ESCAPED:
                self.assertEqual(result, u'\\%s' % six.unichr(i))
            else:
                self.assertEqual(result, six.unichr(i))

    def test_substitutions(self):
        for i in charset.SUBSTITUTE.keys():
            result = charset._qchar(i)

            self.assertEqual(result, charset.SUBSTITUTE[i])

    def test_8bit(self):
        result = charset._qchar(0xf)

        self.assertEqual(result, u'\\x0f')

    def test_16bit(self):
        result = charset._qchar(0x01ff)

        self.assertEqual(result, u'\\u01ff')

    def test_32bit(self):
        result = charset._qchar(0x0001ffff)

        self.assertEqual(result, u'\\U0001ffff')


class TestRngStr(unittest.TestCase):
    def test_1char(self):
        result = charset._rngstr(charset.Range(0x7f, 0x7f))

        self.assertEqual(result, u'\\x7f')

    def test_2char(self):
        result = charset._rngstr(charset.Range(0x7f, 0x80))

        self.assertEqual(result, u'\\x7f\\x80')

    def test_other(self):
        result = charset._rngstr(charset.Range(0x7f, 0x81))

        self.assertEqual(result, u'\\x7f-\\x81')


class TestSearchRanges(unittest.TestCase):
    def test_search_ranges_empty(self):
        ranges = []

        result = charset._search_ranges(ranges, 97)

        self.assertEqual(result, (0, False))

    def test_search_ranges_contained_mid(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 8231)

        self.assertEqual(result, (1, True))

    def test_search_ranges_contained_left(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 98)

        self.assertEqual(result, (0, True))

    def test_search_ranges_contained_right(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 10053)

        self.assertEqual(result, (2, True))

    def test_search_ranges_contained_mid_start(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 8230)

        self.assertEqual(result, (1, True))

    def test_search_ranges_contained_mid_end(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 8232)

        self.assertEqual(result, (1, True))

    def test_search_ranges_uncontained_mid(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 122)

        self.assertEqual(result, (1, False))

    def test_search_ranges_uncontained_left(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 64)

        self.assertEqual(result, (0, False))

    def test_search_ranges_uncontained_right(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 10057)

        self.assertEqual(result, (3, False))

    def test_search_ranges_constrained_lo(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 98, lo=1)

        self.assertEqual(result, (1, False))

    def test_search_ranges_constrained_hi(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = charset._search_ranges(ranges, 10053, hi=2)

        self.assertEqual(result, (2, False))

    def test_search_ranges_low_lo(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        self.assertRaises(IndexError, charset._search_ranges,
                          ranges, 98, lo=-1)

    def test_search_ranges_high_lo(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        self.assertRaises(IndexError, charset._search_ranges,
                          ranges, 98, lo=4)

    def test_search_ranges_high_hi(self):
        ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        self.assertRaises(IndexError, charset._search_ranges,
                          ranges, 98, hi=4)


class TestAddRange(unittest.TestCase):
    def test_contained(self):
        ranges = [
            charset.Range(97, 122),
        ]

        result = charset._add_range(ranges, 98, 121)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 122),
        ])

    def test_disjoint_left(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 97, 98)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 98),
            charset.Range(100, 102),
            charset.Range(110, 112),
        ])

    def test_disjoint_middle(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 104, 108)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(100, 102),
            charset.Range(104, 108),
            charset.Range(110, 112),
        ])

    def test_disjoint_right(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 114, 118)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(100, 102),
            charset.Range(110, 112),
            charset.Range(114, 118),
        ])

    def test_mergable_left_adjacent(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 97, 99)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 102),
            charset.Range(110, 112),
        ])

    def test_mergable_left_contained(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 97, 101)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 102),
            charset.Range(110, 112),
        ])

    def test_mergable_left_overlap(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 97, 103)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 103),
            charset.Range(110, 112),
        ])

    def test_mergable_right_adjacent(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 103, 106)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(100, 106),
            charset.Range(110, 112),
        ])

    def test_mergable_right_contained(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 101, 106)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(100, 106),
            charset.Range(110, 112),
        ])

    def test_mergable_right_overlap(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 99, 106)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(99, 106),
            charset.Range(110, 112),
        ])

    def test_mergable_span_adjacent(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 103, 109)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(100, 112),
        ])

    def test_mergable_span_contained(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 101, 111)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(100, 112),
        ])

    def test_mergable_span_overlap(self):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 99, 113)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(99, 113),
        ])

    @mock.patch.object(charset, '_search_ranges')
    def test_hints(self, mock_search_ranges):
        ranges = [
            charset.Range(100, 102),
            charset.Range(110, 112),
        ]

        result = charset._add_range(ranges, 101, 111, (0, True), (1, True))

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(100, 112),
        ])
        self.assertFalse(mock_search_ranges.called)


class TestDiscardRange(unittest.TestCase):
    def test_uncontained(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(110, 118),
        ]

        result = charset._discard_range(ranges, 105, 109)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 104),
            charset.Range(110, 118),
        ])

    def test_split_left_contained(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = charset._discard_range(ranges, 95, 102)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(103, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ])

    def test_split_left_whole(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = charset._discard_range(ranges, 95, 104)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(108, 112),
            charset.Range(118, 122),
        ])

    def test_split_right_contained(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = charset._discard_range(ranges, 102, 106)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 101),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ])

    def test_split_right_whole(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = charset._discard_range(ranges, 97, 106)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(108, 112),
            charset.Range(118, 122),
        ])

    def test_split_whole(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = charset._discard_range(ranges, 95, 106)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(108, 112),
            charset.Range(118, 122),
        ])

    def test_split_span(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = charset._discard_range(ranges, 100, 120)

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 99),
            charset.Range(121, 122),
        ])

    @mock.patch.object(charset, '_search_ranges')
    def test_hints(self, mock_search_ranges):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = charset._discard_range(ranges, 100, 120,
                                        (0, True), (2, True))

        self.assertIs(result, ranges)
        self.assertEqual(ranges, [
            charset.Range(97, 99),
            charset.Range(121, 122),
        ])
        self.assertFalse(mock_search_ranges.called)


class TestInvert(unittest.TestCase):
    def test_invert_short(self):
        ranges = [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ]

        result = list(charset._invert(ranges))

        self.assertEqual(result, [
            charset.Range(0, 96),
            charset.Range(105, 107),
            charset.Range(113, 117),
            charset.Range(123, charset.MAX_CHAR),
        ])

    def test_invert_long(self):
        ranges = [
            charset.Range(0, 96),
            charset.Range(105, 107),
            charset.Range(113, 117),
            charset.Range(123, charset.MAX_CHAR),
        ]

        result = list(charset._invert(ranges))

        self.assertEqual(result, [
            charset.Range(97, 104),
            charset.Range(108, 112),
            charset.Range(118, 122),
        ])


class TestIntersection(unittest.TestCase):
    def test_short_long(self):
        ranges1 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]
        ranges2 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]

        result = charset._intersection(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(98, 106),
            charset.Range(111, 115),
            charset.Range(117, 122),
        ])

    def test_long_short(self):
        ranges1 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]
        ranges2 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]

        result = charset._intersection(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(98, 106),
            charset.Range(111, 115),
            charset.Range(117, 122),
        ])


class TestUnion(unittest.TestCase):
    def test_short_long(self):
        ranges1 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]
        ranges2 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]

        result = charset._union(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(97, 107),
            charset.Range(110, 122),
        ])

    def test_long_short(self):
        ranges1 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]
        ranges2 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]

        result = charset._union(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(97, 107),
            charset.Range(110, 122),
        ])


class TestDifference(unittest.TestCase):
    def test_short_long(self):
        ranges1 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]
        ranges2 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]

        result = charset._difference(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(97, 97),
            charset.Range(116, 116),
        ])

    def test_long_short(self):
        ranges1 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]
        ranges2 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]

        result = charset._difference(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(107, 107),
            charset.Range(110, 110),
        ])


class TestSymDifference(unittest.TestCase):
    def test_short_long(self):
        ranges1 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]
        ranges2 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]

        result = charset._sym_difference(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(97, 97),
            charset.Range(107, 107),
            charset.Range(110, 110),
            charset.Range(116, 116),
        ])

    def test_long_short(self):
        ranges1 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]
        ranges2 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]

        result = charset._sym_difference(ranges1, ranges2)

        self.assertEqual(result, [
            charset.Range(97, 97),
            charset.Range(107, 107),
            charset.Range(110, 110),
            charset.Range(116, 116),
        ])


class TestIsDisjoint(unittest.TestCase):
    def test_short_long_overlap(self):
        ranges1 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]
        ranges2 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]

        result = charset._isdisjoint(ranges1, ranges2)

        self.assertFalse(result)

    def test_short_long_disjoint(self):
        ranges1 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]
        ranges2 = [
            charset.Range(95, 96),
            charset.Range(107, 110),
            charset.Range(123, 180),
        ]

        result = charset._isdisjoint(ranges1, ranges2)

        self.assertTrue(result)

    def test_long_short_overlap(self):
        ranges1 = [
            charset.Range(98, 107),
            charset.Range(110, 115),
            charset.Range(117, 122),
        ]
        ranges2 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]

        result = charset._isdisjoint(ranges1, ranges2)

        self.assertFalse(result)

    def test_long_short_disjoint(self):
        ranges1 = [
            charset.Range(95, 96),
            charset.Range(107, 110),
            charset.Range(123, 180),
        ]
        ranges2 = [
            charset.Range(97, 106),
            charset.Range(111, 122),
        ]

        result = charset._isdisjoint(ranges1, ranges2)

        self.assertTrue(result)


class CharSetForTest(charset.BaseCharSet):
    def __init__(self, ranges):
        super(CharSetForTest, self).__init__(ranges)


class TestBaseCharSet(unittest.TestCase):
    @mock.patch.object(CharSetForTest, '__init__', return_value=None)
    def test_disjoint(self, mock_init):
        csets = [
            mock.Mock(ranges=[charset.Range(0, 5)]),
            mock.Mock(ranges=[charset.Range(0, 5)]),
            mock.Mock(ranges=[charset.Range(0, 3)]),
            mock.Mock(ranges=[charset.Range(2, 4)]),
            mock.Mock(ranges=[charset.Range(7, 9)]),
        ]

        result = list(CharSetForTest.disjoint(*csets))

        self.assertEqual([i[1] for i in result], [
            [csets[2], csets[0], csets[1]],            # 0-1
            [csets[2], csets[3], csets[0], csets[1]],  # 2-3
            [csets[3], csets[0], csets[1]],            # 4-4
            [csets[0], csets[1]],                      # 5-5
            [csets[4]],                                # 7-9
        ])
        mock_init.assert_has_calls([
            mock.call(0, 1),
            mock.call(2, 3),
            mock.call(4, 4),
            mock.call(5, 5),
            mock.call(7, 9),
        ])
        self.assertEqual(mock_init.call_count, 5)

    def test_init(self):
        obj = CharSetForTest('ranges')

        self.assertEqual(obj.ranges, 'ranges')
        self.assertIsNone(obj._len_cache)

    @mock.patch.object(charset.BaseCharSet, '__contains__', return_value=False)
    @mock.patch.object(charset.BaseCharSet, '__len__', return_value=0)
    def test_str_empty(self, mock_len, mock_contains):
        obj = CharSetForTest([])

        self.assertEqual(str(obj), u'[]')

    @mock.patch.object(charset.BaseCharSet, '__contains__', return_value=False)
    @mock.patch.object(charset.BaseCharSet, '__len__',
                       return_value=charset.FULL_LENGTH)
    def test_str_complete(self, mock_len, mock_contains):
        obj = CharSetForTest([])

        self.assertEqual(str(obj), u'[^]')

    @mock.patch.object(charset.BaseCharSet, '__contains__', return_value=False)
    @mock.patch.object(charset.BaseCharSet, '__len__',
                       return_value=charset.FULL_LENGTH - 1)
    def test_str_dot(self, mock_len, mock_contains):
        obj = CharSetForTest([])

        self.assertEqual(str(obj), u'.')

    @mock.patch.object(charset.BaseCharSet, '__contains__', return_value=True)
    @mock.patch.object(charset.BaseCharSet, '__len__',
                       return_value=charset.FULL_LENGTH - 1)
    def test_str_exclude(self, mock_len, mock_contains):
        obj = CharSetForTest([
            charset.Range(0, 96),
            charset.Range(98, charset.MAX_CHAR),
        ])

        self.assertEqual(str(obj), u'[^a]')

    @mock.patch.object(charset.BaseCharSet, '__contains__', return_value=True)
    @mock.patch.object(charset.BaseCharSet, '__len__', return_value=1)
    def test_str_include(self, mock_len, mock_contains):
        obj = CharSetForTest([
            charset.Range(97, 99),
            charset.Range(102, 104),
        ])

        self.assertEqual(str(obj), u'[a-cf-h]')

    @mock.patch.object(charset, '_search_ranges',
                       return_value=(1, True))
    def test_contains_char(self, mock_search_ranges):
        obj = CharSetForTest([])

        result = obj.__contains__(u'\u2026')

        self.assertIs(result, True)
        mock_search_ranges.assert_called_once_with(obj.ranges, 8230)

    @mock.patch.object(charset, '_search_ranges',
                       return_value=(1, True))
    def test_contains_int(self, mock_search_ranges):
        obj = CharSetForTest([])

        result = obj.__contains__(97)

        self.assertIs(result, True)
        mock_search_ranges.assert_called_once_with(obj.ranges, 97)

    def test_iter(self):
        obj = CharSetForTest([
            charset.Range(97, 99),
            charset.Range(8230, 8232),
        ])

        result = list(obj.__iter__())

        self.assertEqual(result, [
            u'a', u'b', u'c',
            u'\u2026', u'\u2027', u'\u2028',
        ])

    def test_len_empty_uncached(self):
        obj = CharSetForTest([])

        result = obj.__len__()

        self.assertEqual(result, 0)
        self.assertEqual(obj._len_cache, 0)

    def test_len_full_uncached(self):
        obj = CharSetForTest([
            charset.Range(97, 99),
            charset.Range(8230, 8232),
        ])

        result = obj.__len__()

        self.assertEqual(result, 6)
        self.assertEqual(obj._len_cache, 6)

    def test_len_cached(self):
        obj = CharSetForTest([])
        obj._len_cache = 7

        result = obj.__len__()

        self.assertEqual(result, 7)
        self.assertEqual(obj._len_cache, 7)

    def test_eq_equal(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__eq__(obj2)

        self.assertTrue(result)

    def test_eq_altlength(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__eq__(obj2)

        self.assertFalse(result)

    def test_eq_altrange(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 109),
        ])

        result = obj1.__eq__(obj2)

        self.assertFalse(result)

    def test_eq_set_equal(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijkl')

        result = obj1.__eq__(obj2)

        self.assertTrue(result)

    def test_eq_set_unequal(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijklm')

        result = obj1.__eq__(obj2)

        self.assertFalse(result)

    def test_ne_equal(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__ne__(obj2)

        self.assertFalse(result)

    def test_ne_altlength(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__ne__(obj2)

        self.assertTrue(result)

    def test_ne_altrange(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 109),
        ])

        result = obj1.__ne__(obj2)

        self.assertTrue(result)

    def test_ne_set_equal(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijkl')

        result = obj1.__ne__(obj2)

        self.assertFalse(result)

    def test_ne_set_unequal(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijklm')

        result = obj1.__ne__(obj2)

        self.assertTrue(result)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_le_equal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__le__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_le_unequal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__le__(obj2)

        self.assertEqual(result, 'subset')
        mock_issubset.assert_called_once_with(obj2)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_le_set_proper_subset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijklm')

        result = obj1.__le__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_le_set_equal_subset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijkl')

        result = obj1.__le__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_le_set_not_subset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijk')

        result = obj1.__le__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_lt_equal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__lt__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_lt_unequal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__lt__(obj2)

        self.assertEqual(result, 'subset')
        mock_issubset.assert_called_once_with(obj2)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_lt_set_proper_subset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijklm')

        result = obj1.__lt__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_lt_set_equal_subset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijkl')

        result = obj1.__lt__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_lt_set_not_subset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijk')

        result = obj1.__lt__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_ge_equal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__ge__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_ge_unequal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__ge__(obj2)

        self.assertEqual(result, 'subset')
        mock_issubset.assert_called_once_with(obj1)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_ge_set_proper_superset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijk')

        result = obj1.__ge__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_ge_set_equal_superset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijkl')

        result = obj1.__ge__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_ge_set_not_superset_long(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijklm')

        result = obj1.__ge__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_ge_set_not_superset_unequal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijkm')

        result = obj1.__ge__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_ge_not_set(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = 'abcdefhijkm'

        result = obj1.__ge__(obj2)

        self.assertIs(result, NotImplemented)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_gt_equal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__gt__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_gt_unequal(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__gt__(obj2)

        self.assertEqual(result, 'subset')
        mock_issubset.assert_called_once_with(obj1)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_gt_set_proper_superset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijk')

        result = obj1.__gt__(obj2)

        self.assertIs(result, True)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_gt_set_equal_superset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijkl')

        result = obj1.__gt__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_gt_set_not_superset(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = set('abcdefhijklm')

        result = obj1.__gt__(obj2)

        self.assertIs(result, False)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset.BaseCharSet, '_issubset', return_value='subset')
    def test_gt_not_set(self, mock_issubset):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = 'abcdefhijklm'

        result = obj1.__gt__(obj2)

        self.assertIs(result, NotImplemented)
        self.assertFalse(mock_issubset.called)

    @mock.patch.object(charset, '_invert', return_value='inverted')
    def test_invert(self, mock_invert):
        obj = CharSetForTest('ranges')

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj.__invert__()

        self.assertIsInstance(result, charset.BaseCharSet)
        mock_invert.assert_called_once_with('ranges')
        mock_init.assert_called_once_with(None, 'inverted')

    @mock.patch.object(charset.collections.Set, '__and__')
    @mock.patch.object(charset, '_intersection')
    def test_and_equal(self, mock_intersection, mock_and):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__and__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        self.assertFalse(mock_intersection.called)
        mock_init.assert_called_once_with(obj1)
        self.assertFalse(mock_and.called)

    @mock.patch.object(charset.collections.Set, '__and__')
    @mock.patch.object(charset, '_intersection')
    def test_and_unequal(self, mock_intersection, mock_and):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__and__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        mock_intersection.assert_called_once_with(obj1.ranges, obj2.ranges)
        mock_init.assert_called_once_with(None, mock_intersection.return_value)
        self.assertFalse(mock_and.called)

    @mock.patch.object(charset.collections.Set, '__and__')
    @mock.patch.object(charset, '_intersection')
    def test_and_other(self, mock_intersection, mock_and):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = 'other'

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__and__(obj2)

        self.assertEqual(result, mock_and.return_value)
        self.assertFalse(mock_intersection.called)
        self.assertFalse(mock_init.called)
        mock_and.assert_called_once_with('other')

    @mock.patch.object(charset.collections.Set, '__or__')
    @mock.patch.object(charset, '_union')
    def test_or_equal(self, mock_union, mock_or):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__or__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        self.assertFalse(mock_union.called)
        mock_init.assert_called_once_with(obj1)
        self.assertFalse(mock_or.called)

    @mock.patch.object(charset.collections.Set, '__or__')
    @mock.patch.object(charset, '_union')
    def test_or_unequal(self, mock_union, mock_or):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__or__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        mock_union.assert_called_once_with(obj1.ranges, obj2.ranges)
        mock_init.assert_called_once_with(None, mock_union.return_value)
        self.assertFalse(mock_or.called)

    @mock.patch.object(charset.collections.Set, '__or__')
    @mock.patch.object(charset, '_union')
    def test_or_other(self, mock_union, mock_or):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = 'other'

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__or__(obj2)

        self.assertEqual(result, mock_or.return_value)
        self.assertFalse(mock_union.called)
        self.assertFalse(mock_init.called)
        mock_or.assert_called_once_with('other')

    @mock.patch.object(charset.collections.Set, '__sub__')
    @mock.patch.object(charset, '_difference')
    def test_sub_equal(self, mock_difference, mock_sub):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__sub__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        self.assertFalse(mock_difference.called)
        mock_init.assert_called_once_with()
        self.assertFalse(mock_sub.called)

    @mock.patch.object(charset.collections.Set, '__sub__')
    @mock.patch.object(charset, '_difference')
    def test_sub_unequal(self, mock_difference, mock_sub):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__sub__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        mock_difference.assert_called_once_with(obj1.ranges, obj2.ranges)
        mock_init.assert_called_once_with(None, mock_difference.return_value)
        self.assertFalse(mock_sub.called)

    @mock.patch.object(charset.collections.Set, '__sub__')
    @mock.patch.object(charset, '_difference')
    def test_sub_other(self, mock_difference, mock_sub):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = 'other'

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__sub__(obj2)

        self.assertEqual(result, mock_sub.return_value)
        self.assertFalse(mock_difference.called)
        self.assertFalse(mock_init.called)
        mock_sub.assert_called_once_with('other')

    @mock.patch.object(charset.collections.Set, '__xor__')
    @mock.patch.object(charset, '_sym_difference')
    def test_xor_equal(self, mock_sym_difference, mock_xor):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__xor__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        self.assertFalse(mock_sym_difference.called)
        mock_init.assert_called_once_with()
        self.assertFalse(mock_xor.called)

    @mock.patch.object(charset.collections.Set, '__xor__')
    @mock.patch.object(charset, '_sym_difference')
    def test_xor_unequal(self, mock_sym_difference, mock_xor):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__xor__(obj2)

        self.assertIsInstance(result, charset.BaseCharSet)
        mock_sym_difference.assert_called_once_with(obj1.ranges, obj2.ranges)
        mock_init.assert_called_once_with(
            None, mock_sym_difference.return_value)
        self.assertFalse(mock_xor.called)

    @mock.patch.object(charset.collections.Set, '__xor__')
    @mock.patch.object(charset, '_sym_difference')
    def test_xor_other(self, mock_sym_difference, mock_xor):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = 'other'

        with mock.patch.object(CharSetForTest, '__init__',
                               return_value=None) as mock_init:
            result = obj1.__xor__(obj2)

        self.assertEqual(result, mock_xor.return_value)
        self.assertFalse(mock_sym_difference.called)
        self.assertFalse(mock_init.called)
        mock_xor.assert_called_once_with('other')

    def test_issubset_equal(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1._issubset(obj2)

        self.assertTrue(result)

    def test_issubset_subset(self):
        obj1 = CharSetForTest([
            charset.Range(97, 101),
            charset.Range(105, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(96, 102),
            charset.Range(104, 109),
        ])

        result = obj1._issubset(obj2)

        self.assertTrue(result)

    def test_issubset_superset(self):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(98, 101),
            charset.Range(103, 107),
        ])

        result = obj1._issubset(obj2)

        self.assertFalse(result)

    @mock.patch.object(charset.collections.Set, 'isdisjoint')
    @mock.patch.object(charset, '_isdisjoint', return_value='disjoint')
    def test_isdisjoint_charset(self, mock_cs_isdisjoint, mock_set_isdisjoint):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = CharSetForTest([
            charset.Range(103, 103),
            charset.Range(109, 122),
        ])

        result = obj1.isdisjoint(obj2)

        self.assertEqual(result, 'disjoint')
        mock_cs_isdisjoint.assert_called_once_with(obj1.ranges, obj2.ranges)
        self.assertFalse(mock_set_isdisjoint.called)

    @mock.patch.object(charset.collections.Set, 'isdisjoint')
    @mock.patch.object(charset, '_isdisjoint', return_value='disjoint')
    def test_isdisjoint_other(self, mock_cs_isdisjoint, mock_set_isdisjoint):
        obj1 = CharSetForTest([
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])
        obj2 = 'other'

        result = obj1.isdisjoint(obj2)

        self.assertEqual(result, mock_set_isdisjoint.return_value)
        self.assertFalse(mock_cs_isdisjoint.called)
        mock_set_isdisjoint.assert_called_once_with('other')


class TestCharSet(unittest.TestCase):
    @mock.patch.object(charset.CharSet, 'add')
    def test_init_base(self, mock_add):
        result = charset.CharSet()

        self.assertEqual(result.ranges, [])
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_range_list(self, mock_add):
        result = charset.CharSet(None, 'ranges')

        self.assertEqual(result.ranges, ['r', 'a', 'n', 'g', 'e', 's'])
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_start_int(self, mock_add):
        result = charset.CharSet(5)

        self.assertEqual(result.ranges, [charset.Range(5, 5)])
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_start_end_int(self, mock_add):
        result = charset.CharSet(5, 10)

        self.assertEqual(result.ranges, [charset.Range(5, 10)])
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_bad_range_int(self, mock_add):
        self.assertRaises(ValueError, charset.CharSet, 10, 5)
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_start_char(self, mock_add):
        result = charset.CharSet('a')

        self.assertEqual(result.ranges, [charset.Range(97, 97)])
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_start_end_char(self, mock_add):
        result = charset.CharSet('a', 'z')

        self.assertEqual(result.ranges, [charset.Range(97, 122)])
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_bad_range_char(self, mock_add):
        self.assertRaises(ValueError, charset.CharSet, 'z', 'a')
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_unicode_char(self, mock_add):
        result = charset.CharSet(u'\u2026')

        self.assertEqual(result.ranges, [charset.Range(8230, 8230)])
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_tuple(self, mock_add):
        result = charset.CharSet((5, 10))

        self.assertEqual(result.ranges, [charset.Range(5, 10)])
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_charset(self, mock_add):
        obj = CharSetForTest('ranges')

        result = charset.CharSet(obj)

        self.assertEqual(result.ranges, ['r', 'a', 'n', 'g', 'e', 's'])
        self.assertFalse(mock_add.called)

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_seq(self, mock_add):
        result = charset.CharSet([5, 10, 15])

        # Since we mock out .add()
        self.assertEqual(result.ranges, [])
        mock_add.assert_has_calls([
            mock.call(5),
            mock.call(10),
            mock.call(15),
        ])
        self.assertEqual(mock_add.call_count, 3)

    @mock.patch.object(charset.collections.MutableSet, '__iand__')
    @mock.patch.object(charset, '_intersection')
    def test_iand_equal(self, mock_intersection, mock_iand):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__iand__(obj2)

        self.assertIs(result, obj1)
        self.assertFalse(mock_intersection.called)
        self.assertEqual(obj1.ranges, ranges1)
        self.assertEqual(obj1._len_cache, 'len')
        self.assertFalse(mock_iand.called)

    @mock.patch.object(charset.collections.MutableSet, '__iand__')
    @mock.patch.object(charset, '_intersection')
    def test_iand_unequal(self, mock_intersection, mock_iand):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__iand__(obj2)

        self.assertIs(result, obj1)
        mock_intersection.assert_called_once_with(ranges1, obj2.ranges)
        self.assertEqual(obj1.ranges, mock_intersection.return_value)
        self.assertIsNone(obj1._len_cache)
        self.assertFalse(mock_iand.called)

    @mock.patch.object(charset.collections.MutableSet, '__iand__')
    @mock.patch.object(charset, '_intersection')
    def test_iand_other(self, mock_intersection, mock_iand):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = 'other'

        result = obj1.__iand__(obj2)

        self.assertIs(result, mock_iand.return_value)
        self.assertFalse(mock_intersection.called)
        self.assertEqual(obj1._len_cache, 'len')
        mock_iand.assert_called_once_with('other')

    @mock.patch.object(charset.collections.MutableSet, '__ior__')
    @mock.patch.object(charset, '_union')
    def test_ior_equal(self, mock_union, mock_ior):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__ior__(obj2)

        self.assertIs(result, obj1)
        self.assertFalse(mock_union.called)
        self.assertEqual(obj1.ranges, ranges1)
        self.assertEqual(obj1._len_cache, 'len')
        self.assertFalse(mock_ior.called)

    @mock.patch.object(charset.collections.MutableSet, '__ior__')
    @mock.patch.object(charset, '_union')
    def test_ior_unequal(self, mock_union, mock_ior):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__ior__(obj2)

        self.assertIs(result, obj1)
        mock_union.assert_called_once_with(ranges1, obj2.ranges)
        self.assertEqual(obj1.ranges, mock_union.return_value)
        self.assertIsNone(obj1._len_cache)
        self.assertFalse(mock_ior.called)

    @mock.patch.object(charset.collections.MutableSet, '__ior__')
    @mock.patch.object(charset, '_union')
    def test_ior_other(self, mock_union, mock_ior):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = 'other'

        result = obj1.__ior__(obj2)

        self.assertIs(result, mock_ior.return_value)
        self.assertFalse(mock_union.called)
        self.assertEqual(obj1._len_cache, 'len')
        mock_ior.assert_called_once_with('other')

    @mock.patch.object(charset.collections.MutableSet, '__isub__')
    @mock.patch.object(charset, '_difference')
    def test_isub_equal(self, mock_difference, mock_isub):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__isub__(obj2)

        self.assertIs(result, obj1)
        self.assertFalse(mock_difference.called)
        self.assertEqual(obj1.ranges, [])
        self.assertIsNone(obj1._len_cache)
        self.assertFalse(mock_isub.called)

    @mock.patch.object(charset.collections.MutableSet, '__isub__')
    @mock.patch.object(charset, '_difference')
    def test_isub_unequal(self, mock_difference, mock_isub):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__isub__(obj2)

        self.assertIs(result, obj1)
        mock_difference.assert_called_once_with(ranges1, obj2.ranges)
        self.assertEqual(obj1.ranges, mock_difference.return_value)
        self.assertIsNone(obj1._len_cache)
        self.assertFalse(mock_isub.called)

    @mock.patch.object(charset.collections.MutableSet, '__isub__')
    @mock.patch.object(charset, '_difference')
    def test_isub_other(self, mock_difference, mock_isub):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = 'other'

        result = obj1.__isub__(obj2)

        self.assertIs(result, mock_isub.return_value)
        self.assertFalse(mock_difference.called)
        self.assertEqual(obj1._len_cache, 'len')
        mock_isub.assert_called_once_with('other')

    @mock.patch.object(charset.collections.MutableSet, '__ixor__')
    @mock.patch.object(charset, '_sym_difference')
    def test_ixor_equal(self, mock_sym_difference, mock_ixor):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ])

        result = obj1.__ixor__(obj2)

        self.assertIs(result, obj1)
        self.assertFalse(mock_sym_difference.called)
        self.assertEqual(obj1.ranges, [])
        self.assertIsNone(obj1._len_cache)
        self.assertFalse(mock_ixor.called)

    @mock.patch.object(charset.collections.MutableSet, '__ixor__')
    @mock.patch.object(charset, '_sym_difference')
    def test_ixor_unequal(self, mock_sym_difference, mock_ixor):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = charset.CharSet(None, [
            charset.Range(97, 102),
            charset.Range(104, 108),
            charset.Range(110, 118),
        ])

        result = obj1.__ixor__(obj2)

        self.assertIs(result, obj1)
        mock_sym_difference.assert_called_once_with(ranges1, obj2.ranges)
        self.assertEqual(obj1.ranges, mock_sym_difference.return_value)
        self.assertIsNone(obj1._len_cache)
        self.assertFalse(mock_ixor.called)

    @mock.patch.object(charset.collections.MutableSet, '__ixor__')
    @mock.patch.object(charset, '_sym_difference')
    def test_ixor_other(self, mock_sym_difference, mock_ixor):
        ranges1 = [
            charset.Range(97, 102),
            charset.Range(104, 108),
        ]
        obj1 = charset.CharSet(None, ranges1)
        obj1._len_cache = 'len'
        obj2 = 'other'

        result = obj1.__ixor__(obj2)

        self.assertIs(result, mock_ixor.return_value)
        self.assertFalse(mock_sym_difference.called)
        self.assertEqual(obj1._len_cache, 'len')
        mock_ixor.assert_called_once_with('other')

    @mock.patch.object(charset, '_add_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, True))
    def test_add_contained_char(self, mock_search_ranges, mock_add_range):
        obj = charset.CharSet()
        obj._len_cache = 'len'

        obj.add(u'\u2026')

        self.assertEqual(obj._len_cache, 'len')
        mock_search_ranges.assert_called_once_with(obj.ranges, 8230)
        self.assertFalse(mock_add_range.called)

    @mock.patch.object(charset, '_add_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, True))
    def test_add_contained_int(self, mock_search_ranges, mock_add_range):
        obj = charset.CharSet()
        obj._len_cache = 'len'

        obj.add(8230)

        self.assertEqual(obj._len_cache, 'len')
        mock_search_ranges.assert_called_once_with(obj.ranges, 8230)
        self.assertFalse(mock_add_range.called)

    @mock.patch.object(charset, '_add_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, False))
    def test_add_uncontained(self, mock_search_ranges, mock_add_range):
        obj = charset.CharSet()
        obj._len_cache = 'len'

        obj.add(8230)

        self.assertIsNone(obj._len_cache)
        mock_search_ranges.assert_called_once_with(obj.ranges, 8230)
        mock_add_range.assert_called_once_with(
            obj.ranges, 8230, 8230, (0, False), (0, False))

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, False))
    def test_discard_empty(self, mock_search_ranges, mock_discard_range):
        obj = charset.CharSet()
        obj._len_cache = 'len'

        obj.discard(u'\u2026')

        self.assertEqual(obj._len_cache, 'len')
        self.assertFalse(mock_search_ranges.called)
        self.assertFalse(mock_discard_range.called)

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, False))
    def test_discard_uncontained_char(self, mock_search_ranges,
                                      mock_discard_range):
        obj = charset.CharSet(None, ['ranges'])
        obj._len_cache = 'len'

        obj.discard(u'\u2026')

        self.assertEqual(obj._len_cache, 'len')
        mock_search_ranges.assert_called_once_with(['ranges'], 8230)
        self.assertFalse(mock_discard_range.called)

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, False))
    def test_discard_uncontained_int(self, mock_search_ranges,
                                     mock_discard_range):
        obj = charset.CharSet(None, ['ranges'])
        obj._len_cache = 'len'

        obj.discard(8230)

        self.assertEqual(obj._len_cache, 'len')
        mock_search_ranges.assert_called_once_with(['ranges'], 8230)
        self.assertFalse(mock_discard_range.called)

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, True))
    def test_discard_contained(self, mock_search_ranges, mock_discard_range):
        obj = charset.CharSet(None, ['ranges'])
        obj._len_cache = 'len'

        obj.discard(8230)

        self.assertIsNone(obj._len_cache)
        mock_search_ranges.assert_called_once_with(['ranges'], 8230)
        mock_discard_range.assert_called_once_with(
            ['ranges'], 8230, 8230, (0, True), (0, True))

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, False))
    def test_remove_empty(self, mock_search_ranges, mock_discard_range):
        obj = charset.CharSet()
        obj._len_cache = 'len'

        self.assertRaises(KeyError, obj.remove, u'\u2026')
        self.assertEqual(obj._len_cache, 'len')
        self.assertFalse(mock_search_ranges.called)
        self.assertFalse(mock_discard_range.called)

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, False))
    def test_remove_uncontained_char(self, mock_search_ranges,
                                     mock_discard_range):
        obj = charset.CharSet(None, ['ranges'])
        obj._len_cache = 'len'

        self.assertRaises(KeyError, obj.remove, u'\u2026')
        self.assertEqual(obj._len_cache, 'len')
        mock_search_ranges.assert_called_once_with(['ranges'], 8230)
        self.assertFalse(mock_discard_range.called)

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, False))
    def test_remove_uncontained_int(self, mock_search_ranges,
                                    mock_discard_range):
        obj = charset.CharSet(None, ['ranges'])
        obj._len_cache = 'len'

        self.assertRaises(KeyError, obj.remove, 8230)

        self.assertEqual(obj._len_cache, 'len')
        mock_search_ranges.assert_called_once_with(['ranges'], 8230)
        self.assertFalse(mock_discard_range.called)

    @mock.patch.object(charset, '_discard_range')
    @mock.patch.object(charset, '_search_ranges', return_value=(0, True))
    def test_remove_contained(self, mock_search_ranges, mock_discard_range):
        obj = charset.CharSet(None, ['ranges'])
        obj._len_cache = 'len'

        obj.remove(8230)

        self.assertIsNone(obj._len_cache)
        mock_search_ranges.assert_called_once_with(['ranges'], 8230)
        mock_discard_range.assert_called_once_with(
            ['ranges'], 8230, 8230, (0, True), (0, True))

    @mock.patch.object(charset, '_discard_range')
    def test_pop_empty(self, mock_discard_range):
        obj = charset.CharSet(None, [])
        obj._len_cache = 'len'

        self.assertRaises(KeyError, obj.pop)
        self.assertEqual(obj._len_cache, 'len')
        self.assertFalse(mock_discard_range.called)

    @mock.patch.object(charset, '_discard_range')
    def test_pop_nonempty(self, mock_discard_range):
        ranges = [charset.Range(8230, 8232)]
        obj = charset.CharSet(None, ranges)
        obj._len_cache = 'len'

        result = obj.pop()

        self.assertEqual(result, u'\u2026')
        self.assertIsNone(obj._len_cache)
        mock_discard_range.assert_called_once_with(
            ranges, 8230, 8230, (0, True), (0, True))

    def test_clear(self):
        obj = charset.CharSet(None, ['ranges'])
        obj._len_cache = 'len'

        obj.clear()

        self.assertEqual(obj.ranges, [])
        self.assertIsNone(obj._len_cache)


class TestFrozenCharSet(unittest.TestCase):
    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_base(self, mock_CharSet):
        result = charset.FrozenCharSet()

        self.assertEqual(result.ranges, ())
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_range_list(self, mock_CharSet):
        result = charset.FrozenCharSet(None, 'ranges')

        self.assertEqual(result.ranges, ('r', 'a', 'n', 'g', 'e', 's'))
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_start_int(self, mock_CharSet):
        result = charset.FrozenCharSet(5)

        self.assertEqual(result.ranges, (charset.Range(5, 5),))
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_start_end_int(self, mock_CharSet):
        result = charset.FrozenCharSet(5, 10)

        self.assertEqual(result.ranges, (charset.Range(5, 10),))
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_bad_range_int(self, mock_CharSet):
        self.assertRaises(ValueError, charset.FrozenCharSet, 10, 5)
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_start_char(self, mock_CharSet):
        result = charset.FrozenCharSet('a')

        self.assertEqual(result.ranges, (charset.Range(97, 97),))
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_start_end_char(self, mock_CharSet):
        result = charset.FrozenCharSet('a', 'z')

        self.assertEqual(result.ranges, (charset.Range(97, 122),))
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_bad_range_char(self, mock_CharSet):
        self.assertRaises(ValueError, charset.FrozenCharSet, 'z', 'a')
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_unicode_char(self, mock_CharSet):
        result = charset.FrozenCharSet(u'\u2026')

        self.assertEqual(result.ranges, (charset.Range(8230, 8230),))
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_tuple(self, mock_CharSet):
        result = charset.FrozenCharSet((5, 10))

        self.assertEqual(result.ranges, (charset.Range(5, 10),))
        self.assertIsInstance(result.ranges[0], charset.Range)
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_charset(self, mock_CharSet):
        obj = CharSetForTest('ranges')

        result = charset.FrozenCharSet(obj)

        self.assertEqual(result.ranges, ('r', 'a', 'n', 'g', 'e', 's'))
        self.assertFalse(mock_CharSet.called)

    @mock.patch.object(charset, 'CharSet',
                       return_value=mock.Mock(ranges='ranges'))
    def test_init_seq(self, mock_CharSet):
        result = charset.FrozenCharSet([5, 10, 15])

        # Since we mock out .add()
        self.assertEqual(result.ranges, ('r', 'a', 'n', 'g', 'e', 's'))
        mock_CharSet.assert_called_once_with([5, 10, 15], None)

    def test_hash(self):
        obj = charset.FrozenCharSet(None, ('rng1', 'rng2', 'rng3'))

        result = obj.__hash__()

        self.assertEqual(result, hash(('rng1', 'rng2', 'rng3')))
