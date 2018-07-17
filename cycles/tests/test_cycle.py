from unittest import TestCase
from ..cycle import Cycle
from datetime import datetime
from bson import SON


class TestCreate(TestCase):
    def setUp(self):
        self.c = Cycle('111111B')
        self.c.start()
        self.c.stop()

    def test_process_start(self):
        self.c._starttime = None
        self.c.process_event('{ "Event": {"start": 0}}')
        self.assertIsNotNone(self.c._starttime)

    def test_process_stop(self):
        self.c_stoptime = None
        self.c.process_event('{ "Event": {"stop": 0}}')
        self.assertIsNotNone(self.c._stoptime)

    def test_process_stop_is_none(self):
        self.c._starttime, self.c._stoptime = None, None
        self.c.process_event('{ "Event": {"stop": 0}}')
        self.assertIsNone(self.c._stoptime)

    def test_process_normal(self):
        self.assertIsInstance(self.c._starttime, datetime)
        self.assertIsInstance(self.c._stoptime, datetime)

    def test_iter(self):
        self.assertIsInstance(dict(self.c), dict)

    def test_process_no_stop(self):
        self.c._starttime, self.c._stoptime = None, None
        self.c.process_event('{ "Event": {"stop": 0}}')
        self.assertIs(self.c._starttime, None)
        self.assertIs(self.c._stoptime, None)

    def test_stop_no_stop(self):
        self.c._starttime, self.c._stoptime = None, None
        self.c.stop()
        self.assertIs(self.c._starttime, None)
        self.assertIs(self.c._stoptime, None)

    def test_quiet_valueerror(self):
        self.c.process_event('{"And I\'m": "cow!"}')
        self.c.process_event('blah')
        self.c.process_event(42)

    def test_str(self):
        self.assertIsInstance(str(self.c), str)

    def test_bsons(self):
        self.assertIsInstance(self.c.bsons(), SON)

    def test_jsons(self):
        self.assertIsInstance(self.c.jsons(), str)

    def test_data_set(self):
        self.assertEqual(self.c.data_set().program, '111111B')
        # self.assertEqual(self.c.data_set().job, 'Unknown')
        self.assertEqual(self.c.data_set().qty, 1)
        self.assertEqual(self.c.data_set().setup, False)

    def test_diff(self):
        self.assertEqual(self.c.diff(), self.c._stoptime - self.c._starttime)

    def test_diff_is_none(self):
        self.c._stoptime = None
        self.assertIsNone(self.c.diff())

    def test_register_stop_func(self):
        def testfunc(cycle):
            cycle._program = 'hahaha'

        def testfunc2(cycle):
            cycle._program += 'x'

        c = Cycle('this is a program')
        # import ipdb; ipdb.set_trace()
        c.register_stopfunc(testfunc)
        c.register_stopfunc(testfunc2)
        self.assertEqual(len(c._stopfunctions), 2)
        c.start()
        c.stop()
        c.execute_stopfuncs()
        self.assertEqual(c.program, 'hahahax')
