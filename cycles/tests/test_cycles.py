from unittest import TestCase
from ..cycle import Cycle
from ..cycles import Cycles
from sys import stderr
from datetime import timedelta

class TestCreate(TestCase):
    def setUp(self):
        a, b, c = Cycle('111111A'), Cycle('222222B'), Cycle('333333C')
        self.cycles = Cycles(a, b, c)
        for i in self.cycles:
            i.start()
            i.stop()

    def test_append_and_program_list(self):
        d = Cycle('444444D')
        self.cycles.append(d)
        self.assertTrue('444444D' in self.cycles.program_list)

    def test_len(self):
        self.assertEqual(len(self.cycles), 3)

    def test_iter(self):
        l = [x for x in self.cycles]
        self.assertEqual(len(l), 3)

    def test_remove(self):
        y = [i for i in self.cycles]
        for x in y:
            self.cycles.remove(x)
        self.assertEqual(len(self.cycles), 0)

    def test_average(self):
        for i in self.cycles:
            i._stoptime += timedelta(0, 120, 0)
            self.assertEqual(self.cycles.average_time(), 120)
