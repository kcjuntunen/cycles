from unittest import TestCase
from ..cycle import Cycle
from ..cycles import Cycles

class TestCreate(TestCase):
    def setUp(self):
        a, b, c = Cycle('111111A'), Cycle('222222B'), Cycle('333333C')
        self.cycles = Cycles(a, b, c)

    def test_append_and_program_list(self):
        d = Cycle('444444D')
        self.cycles.append(d)
        self.assertTrue('444444D' in self.cycles.program_list)

    def test_len(self):
        self.assertEqual(len(self.cycles), 3)

    def test_iter(self):
        l = [x for x in self.cycles]
        self.assertEqual(len(l), 3)
