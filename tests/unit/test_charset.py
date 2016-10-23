import unittest

import mock

from plexgen import charset


class TestCharSet(unittest.TestCase):
    @mock.patch.object(charset.CharSet, '__init__', return_value=None)
    def test_disjoint(self, mock_init):
        csets = [
            mock.Mock(ranges=[charset.Range(0, 5)]),
            mock.Mock(ranges=[charset.Range(0, 5)]),
            mock.Mock(ranges=[charset.Range(0, 3)]),
            mock.Mock(ranges=[charset.Range(2, 4)]),
            mock.Mock(ranges=[charset.Range(7, 9)]),
        ]

        result = list(charset.CharSet.disjoint(*csets))

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

    @mock.patch.object(charset.CharSet, 'add')
    def test_init_base(self, mock_add):
        result = charset.CharSet()

        self.assertEqual(result.ranges, [])
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

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, True))
    def test_contains_char(self, mock_search_ranges):
        obj = charset.CharSet()

        result = obj.__contains__(u'\u2026')

        self.assertIs(result, True)
        mock_search_ranges.assert_called_once_with(8230)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, True))
    def test_contains_int(self, mock_search_ranges):
        obj = charset.CharSet()

        result = obj.__contains__(97)

        self.assertIs(result, True)
        mock_search_ranges.assert_called_once_with(97)

    def test_iter(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
        ]

        result = list(obj.__iter__())

        self.assertEqual(result, [
            u'a', u'b', u'c',
            u'\u2026', u'\u2027', u'\u2028',
        ])

    def test_len_empty(self):
        obj = charset.CharSet()

        result = obj.__len__()

        self.assertEqual(result, 0)

    def test_len_full(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
        ]

        result = obj.__len__()

        self.assertEqual(result, 6)

    def test_search_ranges_empty(self):
        obj = charset.CharSet()

        result = obj._search_ranges(97)

        self.assertEqual(result, (0, False))

    def test_search_ranges_contained_mid(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(8231)

        self.assertEqual(result, (1, True))

    def test_search_ranges_contained_left(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(98)

        self.assertEqual(result, (0, True))

    def test_search_ranges_contained_right(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(10053)

        self.assertEqual(result, (2, True))

    def test_search_ranges_contained_mid_start(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(8230)

        self.assertEqual(result, (1, True))

    def test_search_ranges_contained_mid_end(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(8232)

        self.assertEqual(result, (1, True))

    def test_search_ranges_uncontained_mid(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(122)

        self.assertEqual(result, (1, False))

    def test_search_ranges_uncontained_left(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(64)

        self.assertEqual(result, (0, False))

    def test_search_ranges_uncontained_right(self):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 99),
            charset.Range(8230, 8232),
            charset.Range(10052, 10054),
        ]

        result = obj._search_ranges(10057)

        self.assertEqual(result, (3, False))

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(0, True))
    def test_add_contained_char(self, mock_search_ranges):
        obj = charset.CharSet()

        obj.add(u'\u2026')

        self.assertEqual(obj.ranges, [])
        mock_search_ranges.assert_called_once_with(8230)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(0, True))
    def test_add_contained_int(self, mock_search_ranges):
        obj = charset.CharSet()

        obj.add(8230)

        self.assertEqual(obj.ranges, [])
        mock_search_ranges.assert_called_once_with(8230)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(0, False))
    def test_add_empty(self, mock_search_ranges):
        obj = charset.CharSet()

        obj.add(98)

        self.assertEqual(obj.ranges, [charset.Range(98, 98)])
        self.assertIsInstance(obj.ranges[0], charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, False))
    def test_add_extend_left(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 97),
            charset.Range(100, 100),
        ]

        obj.add(98)

        self.assertEqual(obj.ranges, [
            charset.Range(97, 98),
            charset.Range(100, 100),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, False))
    def test_add_extend_right(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 97),
            charset.Range(100, 100),
        ]

        obj.add(99)

        self.assertEqual(obj.ranges, [
            charset.Range(97, 97),
            charset.Range(99, 100),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, False))
    def test_add_merge(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 97),
            charset.Range(99, 99),
        ]

        obj.add(98)

        self.assertEqual(obj.ranges, [charset.Range(97, 99)])
        self.assertIsInstance(obj.ranges[0], charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(0, False))
    def test_add_min_char(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 97),
            charset.Range(99, 99),
        ]

        obj.add(charset.MIN_CHAR)

        self.assertEqual(obj.ranges, [
            charset.Range(charset.MIN_CHAR, charset.MIN_CHAR),
            charset.Range(97, 97),
            charset.Range(99, 99),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(2, False))
    def test_add_max_char(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 97),
            charset.Range(99, 99),
        ]

        obj.add(charset.MAX_CHAR)

        self.assertEqual(obj.ranges, [
            charset.Range(97, 97),
            charset.Range(99, 99),
            charset.Range(charset.MAX_CHAR, charset.MAX_CHAR),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(0, False))
    def test_discard_empty(self, mock_search_ranges):
        obj = charset.CharSet()

        obj.discard('a')

        self.assertEqual(obj.ranges, [])
        self.assertFalse(mock_search_ranges.called)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(0, False))
    def test_discard_uncontained_char(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [charset.Range(97, 99)]

        obj.discard(u'\u2026')

        self.assertEqual(obj.ranges, [charset.Range(97, 99)])
        self.assertIsInstance(obj.ranges[0], charset.Range)
        mock_search_ranges.assert_called_once_with(8230)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(0, False))
    def test_discard_uncontained_int(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [charset.Range(97, 99)]

        obj.discard(8230)

        self.assertEqual(obj.ranges, [charset.Range(97, 99)])
        self.assertIsInstance(obj.ranges[0], charset.Range)
        mock_search_ranges.assert_called_once_with(8230)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, True))
    def test_discard_whole(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 98),
            charset.Range(100, 100),
            charset.Range(102, 103),
        ]

        obj.discard(100)

        self.assertEqual(obj.ranges, [
            charset.Range(97, 98),
            charset.Range(102, 103),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, True))
    def test_discard_left(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 98),
            charset.Range(100, 104),
            charset.Range(106, 107),
        ]

        obj.discard(100)

        self.assertEqual(obj.ranges, [
            charset.Range(97, 98),
            charset.Range(101, 104),
            charset.Range(106, 107),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, True))
    def test_discard_right(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 98),
            charset.Range(100, 104),
            charset.Range(105, 107),
        ]

        obj.discard(104)

        self.assertEqual(obj.ranges, [
            charset.Range(97, 98),
            charset.Range(100, 103),
            charset.Range(105, 107),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)

    @mock.patch.object(charset.CharSet, '_search_ranges',
                       return_value=(1, True))
    def test_discard_middle(self, mock_search_ranges):
        obj = charset.CharSet()
        obj.ranges = [
            charset.Range(97, 98),
            charset.Range(100, 104),
            charset.Range(105, 107),
        ]

        obj.discard(102)

        self.assertEqual(obj.ranges, [
            charset.Range(97, 98),
            charset.Range(100, 101),
            charset.Range(103, 104),
            charset.Range(105, 107),
        ])
        for entry in obj.ranges:
            self.assertIsInstance(entry, charset.Range)
