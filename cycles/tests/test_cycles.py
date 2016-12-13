from unittest import TestCase
from ..cycle import Cycle
from ..machinesetup import MachineSetup
from ..cycles import Cycles
from sys import stderr
from datetime import timedelta


class TestCreate(TestCase):
    def setUp(self):
        sa, sb, sc = (MachineSetup('111111A'), MachineSetup('222222B'),
                      MachineSetup('333333C'))
        a, b, c = Cycle('111111A'), Cycle('222222B'), Cycle('333333C')
        self.cycles = Cycles(sa, a, sb, b, sc, c)
        sa.start()
        sa.stop()
        a.start()
        a.stop()
        sb.start()
        sb.stop()
        b.start()
        b.stop()
        sc.start()
        sc.stop()
        c.start()
        c.stop()

    def test_append_and_program_list(self):
        d = Cycle('444444D')
        self.cycles.append(d)
        self.assertTrue('444444D' in self.cycles.program_list)

    def test_none_append(self):
        a, b = Cycles(), Cycle('182989A')
        a.append(b)
        self.assertEqual(len(a), 1)

    def test_none_program_list(self):
        c = Cycles()
        self.assertIsNone(c.program_list)

    def test_len(self):
        self.assertEqual(len(self.cycles), 6)

    def test_iter(self):
        l = [x for x in self.cycles]
        self.assertEqual(len(l), 6)

    def test_remove(self):
        y = [i for i in self.cycles]
        for x in y:
            self.cycles.remove(x)
        self.assertEqual(len(self.cycles), 0)

    def test_average(self):
        for i in self.cycles:
            if i._stoptime is not None:
                i._stoptime += timedelta(0, 120, 0)
        self.assertEqual(self.cycles.average_time(), 120)

    def test_bsons(self):
        self.assertEqual(len(self.cycles.bsons()), 6)

    def test_jsons(self):
        print(self.cycles.jsons(), stderr)
