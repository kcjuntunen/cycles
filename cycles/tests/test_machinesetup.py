from unittest import TestCase
from ..machinesetup import MachineSetup


class TestCreate(TestCase):
    def test_machine_setup(self):
        program_name = '38288A'
        ms = MachineSetup(program_name)
        self.assertEqual(ms.display_name, '{} Setup'.format(program_name))
