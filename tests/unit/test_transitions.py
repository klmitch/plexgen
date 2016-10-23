import unittest

import mock

from plexgen import transitions


class TransitionForTest(transitions.Transition):
    trans_args = set(['a', 'b', 'c'])
    priority = 3
    defaults = {
        'c': 42,
    }

    @classmethod
    def disjoint(cls, transitions):
        pass

    def match(self, char, sim):
        pass

    def merge(self, others):
        pass


class TestTransition(unittest.TestCase):
    def test_init_base(self):
        result = TransitionForTest('out', 'in', a=1, b=2)

        self.assertEqual(result.state_out, 'out')
        self.assertEqual(result.state_in, 'in')
        self.assertEqual(result.args, {'a': 1, 'b': 2, 'c': 42})

    def test_init_default_override(self):
        result = TransitionForTest('out', 'in', a=1, b=2, c=3)

        self.assertEqual(result.state_out, 'out')
        self.assertEqual(result.state_in, 'in')
        self.assertEqual(result.args, {'a': 1, 'b': 2, 'c': 3})

    def test_init_missing(self):
        self.assertRaises(TypeError, TransitionForTest,
                          'out', 'in', a=1)

    def test_init_extra(self):
        self.assertRaises(TypeError, TransitionForTest,
                          'out', 'in', a=1, b=2, d=4)

    def test_getattr_exists(self):
        obj = TransitionForTest('out', 'in', a=1, b=2)

        self.assertEqual(obj.c, 42)

    def test_getattr_missing(self):
        obj = TransitionForTest('out', 'in', a=1, b=2)

        self.assertRaises(AttributeError, lambda: obj.d)

    def test_reverse(self):
        obj = TransitionForTest('out', 'in', a=1, b=2)

        obj.reverse()

        self.assertEqual(obj.state_out, 'in')
        self.assertEqual(obj.state_in, 'out')


class TestEpsilon(unittest.TestCase):
    def test_disjoint(self):
        result = transitions.Epsilon.disjoint(['t1', 't2', 't3'])

        self.assertEqual(result, [['t1', 't2', 't3']])

    def test_match(self):
        obj = transitions.Epsilon('out', 'in')

        self.assertRaises(TypeError, obj.match, 'a', 'sim')

    def test_merge(self):
        obj = transitions.Epsilon('out', 'in')

        result = obj.merge('others')

        self.assertEqual(result, set([obj]))


class TestMatchChar(unittest.TestCase):
    @mock.patch.object(transitions.charset.CharSet, 'disjoint')
    def test_disjoint(self, mock_disjoint):
        csets = {
            'dj1': mock.Mock(),
            'dj2': mock.Mock(),
            'dj3': mock.Mock(),
            't1': mock.Mock(),
            't2': mock.Mock(),
            't3': mock.Mock(),
            't4': mock.Mock(),
            't5': mock.Mock(),
        }
        trans = [
            transitions.MatchChar('t1_out', 't1_in', cset=csets['t1']),
            transitions.MatchChar('t2_out', 't2_in', cset=csets['t2']),
            transitions.MatchChar('t3_out', 't3_in', cset=csets['t3']),
            transitions.MatchChar('t4_out', 't4_in', cset=csets['t4']),
            transitions.MatchChar('t5_out', 't5_in', cset=csets['t5']),
        ]
        mock_disjoint.return_value = [
            (csets['dj1'], [csets['t1'], csets['t2']]),
            (csets['dj2'], [csets['t2']]),
            (csets['dj3'], [csets['t3'], csets['t4'], csets['t5']]),
        ]
        expected = [
            [
                transitions.MatchChar('t1_out', 't1_in', cset=csets['dj1']),
                transitions.MatchChar('t2_out', 't2_in', cset=csets['dj1']),
            ],
            [
                transitions.MatchChar('t2_out', 't2_in', cset=csets['dj2']),
            ],
            [
                transitions.MatchChar('t3_out', 't3_in', cset=csets['dj3']),
                transitions.MatchChar('t4_out', 't4_in', cset=csets['dj3']),
                transitions.MatchChar('t5_out', 't5_in', cset=csets['dj3']),
            ],
        ]

        for i, trans in enumerate(transitions.MatchChar.disjoint(trans)):
            self.assertEqual(len(trans), len(expected[i]))
            for exp, act in zip(expected[i], trans):
                self.assertEqual(exp.state_out, act.state_out)
                self.assertEqual(exp.state_in, act.state_in)
                self.assertEqual(exp.cset, act.cset)

    def test_match_end(self):
        obj = transitions.MatchChar('out', 'in', cset=set('abc'))
        sim = mock.Mock()

        result = obj.match(None, sim)

        self.assertFalse(result)
        self.assertFalse(sim.consume.called)

    def test_match_with_match(self):
        obj = transitions.MatchChar('out', 'in', cset=set('abc'))
        sim = mock.Mock()

        result = obj.match('b', sim)

        self.assertTrue(result)
        sim.consume.assert_called_once_with()

    def test_match_no_match(self):
        obj = transitions.MatchChar('out', 'in', cset=set('abc'))
        sim = mock.Mock()

        result = obj.match('d', sim)

        self.assertFalse(result)
        self.assertFalse(sim.consume.called)

    def test_merge(self):
        others = set([
            mock.Mock(cset=set('ab')),
            mock.Mock(cset=set('cd')),
            mock.Mock(cset=set('ef')),
        ])
        obj = transitions.MatchChar('out', 'in', cset=set('bfg'))

        result = obj.merge(others)

        self.assertEqual(result, set([obj]))
        self.assertEqual(obj.cset, set('abcdefg'))


class TestAction(unittest.TestCase):
    def test_disjoint(self):
        result = transitions.Action.disjoint(['t1', 't2', 't3'])

        self.assertEqual(result, [['t1'], ['t2'], ['t3']])

    def test_match(self):
        obj = transitions.Action('out', 'in', action='action', precedence=1,
                                 name='act')
        sim = mock.Mock()

        result = obj.match('c', sim)

        self.assertTrue(result)
        sim.assert_has_calls([
            mock.call.get_lexeme(),
            mock.call.start_lexeme(),
            mock.call.action('act', 'action', sim.get_lexeme.return_value),
        ])
        self.assertEqual(len(sim.method_calls), 3)

    def test_merge_lower(self):
        trans = [
            transitions.Action('out', 'in', action='act1', precedence=2),
            transitions.Action('out', 'in', action='act2', precedence=3),
            transitions.Action('out', 'in', action='act3', precedence=4),
        ]
        obj = transitions.Action('out', 'in', action='act', precedence=0)

        result = obj.merge(set(trans))

        self.assertEqual(result, set([obj]))

    def test_merge_higher(self):
        trans = [
            transitions.Action('out', 'in', action='act1', precedence=2),
            transitions.Action('out', 'in', action='act2', precedence=3),
            transitions.Action('out', 'in', action='act3', precedence=4),
        ]
        obj = transitions.Action('out', 'in', action='act', precedence=5)

        result = obj.merge(set(trans))

        self.assertEqual(result, set([trans[0]]))
