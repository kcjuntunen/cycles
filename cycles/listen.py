#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2016 K. C. Juntunen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
import os
from asyncore import file_dispatcher, loop
from serial import Serial
from threading import Thread
import evdev

from cycles.cycle import Cycle
from cycles.cycles import Cycles
from cycles.machinesetup import MachineSetup

CYCLES = Cycles()

SCANCODES = {
    2: '1', 3: '2', 4: '3', 5: '4', 6: '5',
    7: '6', 8: '7', 9: '8', 10: '9', 11: '0',

    16: 'Q', 17: 'W', 18: 'E', 19: 'R', 20: 'T',
    21: 'Y', 22: 'U', 23: 'I', 24: 'O', 25: 'P',

    # 28: 'CRLF',

    30: 'A', 31: 'S', 32: 'D', 33: 'F', 34: 'G',
    35: 'H', 36: 'J', 37: 'K', 38: 'L', 39: ';',

    # 42: 'LSHIFT',

    44: 'Z', 45: 'X', 46: 'C', 47: 'V', 48: 'B',
    49: 'N', 50: 'M', 51: ',', 52: '.', 53: '/',
}


class InputDeviceDispatcher(file_dispatcher):
    """
    Handle scanner.
    """
    def __init__(self, device):
        print("Scanner started.")
        self.device = device
        self.program = ''
        file_dispatcher.__init__(self, device)

    def recv(self, ign=None):
        import pdb; pdb.set_trace()
        print("scanner recv")
        return self.device.read()

    def handle_read(self):
        print("handle scanner")
        global CYCLES
        CYCLES = Cycles(MachineSetup(recv_scanner(self.device)))
        for c in CYCLES:
            print("scan -> %s" % (c))


class SerialDispatcher(file_dispatcher):
    """
    Handle serial.
    """
    def __init__(self, device):
        print("Serial started.")
        self.device = device
        file_dispatcher.__init__(self, device)

    def recv(self, ign=None):
        print("serial recv")
        device.flush()
        import pdb; pdb.set_trace()
        return self.device.read()

    def handle_read(self):
        print("handle serial")
        global CYCLES
        input_string = recv_serial(self.device)
        current_cycle = Cycle(CYCLES[0].program)
        current_cycle.process_event(input_string)
        CYCLES.append(current_cycle)
        for c in CYCLES:
            print("motion -> %s" % (c))


def devlist():
    """
    Return a list of devices accessible to evdev.
    """
    devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    return devices


def print_devlist():
    """
    Just in case I want to print the list.
    """
    for device in devlist():
        print(device.fn, device.name, device.phys)


def get_device(device_names):
    """
    Figure out which device we want.
    """
    # /dev/input/event4
    # WIT Electron Company WIT 122-UFS V2.03
    # usb-0000:00:06.0-1/input0
    device_list = devlist()
    for name in device_names:
        for dev in device_list:
            if name in dev.name:
                return dev.fn


def recv_scanner(device):
    """
    Parse the huge load of stuff that rolls in from the scanner.
    """
    program = ''
    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            data = evdev.categorize(event)
            if data.keystate == 1 and data.scancode != 28:
                keypress = (SCANCODES.get(data.scancode) or '')
                program += keypress
            if data.scancode == evdev.ecodes.KEY_ENTER and program != '':
                ms = MachineSetup(program)
                ms.start()
                return program


def recv_serial(device):
    device.flush()
    strline = device.readline().decode('utf-8').strip()
    print("Got %s" % (strline))
    return strline


def main():
    """
    Main loop.
    """
    try:
        os.system('stty -echo')
        InputDeviceDispatcher(evdev.InputDevice(get_device(['WIT 122-UFS',])))
        ser = Serial("/dev/ttyAMA0", 115200)
        SerialDispatcher(ser)
        loop()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
    finally:
        os.system('stty echo')
        print('Exiting...')

    exit(0)


if __name__ == "__main__":
    main()
