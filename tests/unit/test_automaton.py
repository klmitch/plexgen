import unittest

import mock

from plexgen import automaton


class TestStateMapper(unittest.TestCase):
    def test_init(self):
        src = mock.Mock(_start='src_start')
        dest = mock.Mock(_start='dest_start')

        result = automaton._StateMapper(src, dest)

        self.assertEqual(result, {'src_start': 'dest_start'})
        self.assertEqual(result.src, src)
        self.assertEqual(result.dest, dest)

    def test_init(self):
        src = mock.Mock(_start='src_start')
        dest = mock.Mock(**{
            '_start': 'dest_start',
            '_new_state.return_value': 'new_state',
        })
        key = mock.Mock(accepting='accepting')
        obj = automaton._StateMapper(src, dest)

        result = obj[key]

        self.assertEqual(result, 'new_state')
        self.assertEqual(obj, {
            'src_start': 'dest_start',
            key: 'new_state',
        })
