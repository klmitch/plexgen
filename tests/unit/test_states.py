import unittest

import mock

from plexgen import states


class TestAllEps(unittest.TestCase):
    def test_empty(self):
        result = states._all_eps({})

        self.assertTrue(result)

    def test_only_eps(self):
        tab = {
            0: set('spam'),
            1: set(),
            2: set(),
        }

        result = states._all_eps(tab)

        self.assertTrue(result)

    def test_more_than_eps(self):
        tab = {
            0: set('spam'),
            1: set('spam'),
            2: set('spam'),
        }

        result = states._all_eps(tab)

        self.assertFalse(result)


class TestIterTrans(unittest.TestCase):
    def test_base(self):
        tab = {
            0: set(['0-0', '0-1']),
            1: set(['1-0', '1-1', '1-2']),
            2: set(['2-0']),
        }

        result = list(states._iter_trans(tab, None))

        self.assertEqual(set(result[:2]), set(['0-0', '0-1']))
        self.assertEqual(set(result[2:5]), set(['1-0', '1-1', '1-2']))
        self.assertEqual(set(result[5:]), set(['2-0']))

    def test_prio(self):
        tab = {
            0: set(['0-0', '0-1']),
            1: set(['1-0', '1-1', '1-2']),
            2: set(['2-0']),
        }

        result = set(states._iter_trans(tab, 1))

        self.assertEqual(result, set(['1-0', '1-1', '1-2']))


class TestEpsClosure(unittest.TestCase):
    def test_base(self):
        tstates = {'st%d' % i: mock.Mock() for i in range(8)}
        trans = {
            'st0': ['st1', 'st2'],
            'st1': ['st0'],
            'st1': ['st5'],
            'st3': ['st2', 'st4'],
            'st6': ['st1', 'st7'],
        }
        for st_name, state in tstates.items():
            state.iter_out.return_value = [
                mock.Mock(state_in=tstates[t]) for t in trans.get(st_name, ())
            ]

        result = states.eps_closure(set([tstates['st0'], tstates['st3']]))

        self.assertEqual(
            result,
            frozenset(tstates[st] for st in
                      ['st0', 'st1', 'st2', 'st3', 'st4', 'st5']),
        )
        self.assertIsInstance(result, frozenset)


class TestState(unittest.TestCase):
    def test_init_base(self):
        result = states.State()

        self.assertIs(result.accepting, False)
        self.assertIsNone(result.code)
        self.assertIsNone(result.name)
        self.assertEqual(result._trans_in, {})
        self.assertEqual(result._trans_out, {})
        self.assertIsNone(result._eps_in)
        self.assertIsNone(result._eps_out)

    def test_init_accepting(self):
        result = states.State('accepting', 'code')

        self.assertIs(result.accepting, True)
        self.assertEqual(result.code, 'code')
        self.assertIsNone(result.name)
        self.assertEqual(result._trans_in, {})
        self.assertEqual(result._trans_out, {})
        self.assertIsNone(result._eps_in)
        self.assertIsNone(result._eps_out)

    def test_reverse(self):
        obj = states.State()
        obj._trans_in = 'in'
        obj._trans_out = 'out'

        obj.reverse()

        self.assertEqual(obj._trans_in, 'out')
        self.assertEqual(obj._trans_out, 'in')

    def test_transition_empty(self):
        trans = mock.Mock(**{
            'priority': 1,
            'merge.return_value': None,
        })
        trans_class = mock.Mock(return_value=trans)
        st_from = states.State()
        st_to = states.State()

        st_from.transition(trans_class, st_to, a=1, b=2, c=3)

        trans_class.assert_called_once_with(st_from, st_to, a=1, b=2, c=3)
        trans.merge.assert_called_once_with(set())
        self.assertEqual(st_from._trans_out, {1: set([trans])})
        self.assertEqual(st_to._trans_in, {1: set([trans])})

    def test_transition_nomerge(self):
        trans = mock.Mock(**{
            'priority': 1,
            'merge.return_value': None,
        })
        trans_class = mock.Mock(return_value=trans)
        st_from = states.State()
        st_to = states.State()
        others = set([
            mock.Mock(state_in=st_to),
            mock.Mock(state_in=st_to),
            mock.Mock(state_in=st_to),
        ])
        from_out = set([
            mock.Mock(state_in='st1'),
            mock.Mock(state_in='st2'),
            mock.Mock(state_in='st3'),
        ])
        st_from._trans_out = {
            0: set([0, 1, 2]),
            1: from_out | others,
            2: set([3, 4, 5]),
        }
        to_in = set([
            mock.Mock(),
            mock.Mock(),
            mock.Mock(),
        ])
        st_to._trans_in = {
            0: set([6, 7, 8]),
            1: to_in | others,
            2: set([9, 10, 11]),
        }

        st_from.transition(trans_class, st_to, a=1, b=2, c=3)

        trans_class.assert_called_once_with(st_from, st_to, a=1, b=2, c=3)
        trans.merge.assert_called_once_with(others)
        self.assertEqual(st_from._trans_out, {
            0: set([0, 1, 2]),
            1: from_out | others | set([trans]),
            2: set([3, 4, 5]),
        })
        self.assertEqual(st_to._trans_in, {
            0: set([6, 7, 8]),
            1: to_in | others | set([trans]),
            2: set([9, 10, 11]),
        })

    def test_transition_merge(self):
        trans = mock.Mock(**{
            'priority': 1,
            'merge.return_value': set([12, 13, 14]),
        })
        trans_class = mock.Mock(return_value=trans)
        st_from = states.State()
        st_to = states.State()
        others = set([
            mock.Mock(state_in=st_to),
            mock.Mock(state_in=st_to),
            mock.Mock(state_in=st_to),
        ])
        from_out = set([
            mock.Mock(state_in='st1'),
            mock.Mock(state_in='st2'),
            mock.Mock(state_in='st3'),
        ])
        st_from._trans_out = {
            0: set([0, 1, 2]),
            1: from_out | others,
            2: set([3, 4, 5]),
        }
        to_in = set([
            mock.Mock(),
            mock.Mock(),
            mock.Mock(),
        ])
        st_to._trans_in = {
            0: set([6, 7, 8]),
            1: to_in | others,
            2: set([9, 10, 11]),
        }

        st_from.transition(trans_class, st_to, a=1, b=2, c=3)

        trans_class.assert_called_once_with(st_from, st_to, a=1, b=2, c=3)
        trans.merge.assert_called_once_with(others)
        self.assertEqual(st_from._trans_out, {
            0: set([0, 1, 2]),
            1: from_out | set([12, 13, 14]),
            2: set([3, 4, 5]),
        })
        self.assertEqual(st_to._trans_in, {
            0: set([6, 7, 8]),
            1: to_in | set([12, 13, 14]),
            2: set([9, 10, 11]),
        })

    @mock.patch.object(states, '_iter_trans')
    def test_iter_in_base(self, mock_iter_trans):
        obj = states.State()
        obj._trans_in = 'in'

        result = obj.iter_in()

        self.assertEqual(result, mock_iter_trans.return_value)
        mock_iter_trans.assert_called_once_with('in', None)

    @mock.patch.object(states, '_iter_trans')
    def test_iter_in_prio(self, mock_iter_trans):
        obj = states.State()
        obj._trans_in = 'in'

        result = obj.iter_in(2)

        self.assertEqual(result, mock_iter_trans.return_value)
        mock_iter_trans.assert_called_once_with('in', 2)

    @mock.patch.object(states, '_iter_trans')
    def test_iter_out_base(self, mock_iter_trans):
        obj = states.State()
        obj._trans_out = 'out'

        result = obj.iter_out()

        self.assertEqual(result, mock_iter_trans.return_value)
        mock_iter_trans.assert_called_once_with('out', None)

    @mock.patch.object(states, '_iter_trans')
    def test_iter_out_prio(self, mock_iter_trans):
        obj = states.State()
        obj._trans_out = 'out'

        result = obj.iter_out(2)

        self.assertEqual(result, mock_iter_trans.return_value)
        mock_iter_trans.assert_called_once_with('out', 2)

    @mock.patch.object(states, '_all_eps', return_value='uncached')
    def test_eps_in_cached(self, mock_all_eps):
        obj = states.State()
        obj._trans_in = 'in'
        obj._eps_in = 'cached'

        self.assertEqual(obj.eps_in, 'cached')
        self.assertEqual(obj._eps_in, 'cached')
        self.assertFalse(mock_all_eps.called)

    @mock.patch.object(states, '_all_eps', return_value='uncached')
    def test_eps_in_uncached(self, mock_all_eps):
        obj = states.State()
        obj._trans_in = 'in'

        self.assertEqual(obj.eps_in, 'uncached')
        self.assertEqual(obj._eps_in, 'uncached')
        mock_all_eps.assert_called_once_with('in')

    @mock.patch.object(states, '_all_eps', return_value='uncached')
    def test_eps_out_cached(self, mock_all_eps):
        obj = states.State()
        obj._trans_out = 'out'
        obj._eps_out = 'cached'

        self.assertEqual(obj.eps_out, 'cached')
        self.assertEqual(obj._eps_out, 'cached')
        self.assertFalse(mock_all_eps.called)

    @mock.patch.object(states, '_all_eps', return_value='uncached')
    def test_eps_out_uncached(self, mock_all_eps):
        obj = states.State()
        obj._trans_out = 'out'

        self.assertEqual(obj.eps_out, 'uncached')
        self.assertEqual(obj._eps_out, 'uncached')
        mock_all_eps.assert_called_once_with('out')
