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
import os, stat
from sys import stderr
from asyncore import file_dispatcher, loop
from serial import Serial
from threading import Thread
import evdev
from pymongo import MongoClient
from pickle import Unpickler
from collections import namedtuple
from glob import glob

from cycles.cycle import Cycle
from cycles.cycles import Cycles
from cycles.machinesetup import MachineSetup

st = os.stat('/etc/cycles')

if os.getuid() == st.st_uid:
    try:
        config_file = glob('/etc/cycles/config.*.pickle')[0]
        Config = namedtuple('Config', 'dbhost dbport dbuser dbpwd db collection')
        with open(config_file, 'rb') as fh:
            unpickler = Unpickler(fh)
            c = unpickler.load()
            # Turns out namedtuple's aren't very useful.
            # I probably won't bother with them again.
            CONFIG = Config(c['dbhost'], c['dbport'], c['dbuser'], c['dbpwd'], c['db'], c['collection'])
    except IndexError:
        print("No config file found.", file=stderr)
        exit(1)
    except Exception as e:
        print(e, file=stderr)
        exit(1)
else:
    raise PermissionError('Cannot access /etc/cycles')

SETUP = MachineSetup('STUB')
CYCLE = Cycle('STUB')
CYCLES = Cycles()
POLL_ARGS = {"comm": "go", }
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
        # print("Scanner started.")
        self.device = device
        self.program = ''
        file_dispatcher.__init__(self, device)

    def recv(self, ign=None):
        # print("scanner recv")
        return self.device.read()

    def handle_read(self):
        # print("handle scanner")
        global CYCLES
        global SETUP
        SETUP = MachineSetup(recv_scanner(self.device))
        CYCLES = Cycles(SETUP)
        SETUP.register_stopfunc(insert_and_remove)
        # for c in SETUP, CYCLE:
        #     print("scan -> %s" % (c))


def insert_and_remove(cyc):
    uri = 'mongodb://%s:%s@%s:%s/%s' % (CONFIG.dbuser, CONFIG.dbpwd,
                                        CONFIG.dbhost, CONFIG.dbport,
                                        CONFIG.db)
    m = MongoClient(uri)
    db = m.get_database(CONFIG.db)
    tc = db.get_collection(CONFIG.collection)
    # print("%s.%s.%s" % (CONFIG.dbhost, CONFIG.db, CONFIG.collection))
    if cyc.stoptime is not None and cyc.starttime is not None:
        tc.insert_one(cyc.bsons())
        # print("insert -> %s, diff: %s" % (cyc, cyc.diff()))
        CYCLES.remove(cyc)

class SerialThread(Thread):
    def __init__(self, ser):
        Thread.__init__(self)
        self.ser = ser
    def run(self):
        serial_loop(self.ser)


def serial_loop(ser):
    print('serial started')
    global CYCLE
    while True:
        if POLL_ARGS["comm"] == "stop":
            exit(0)
        line = ser.readline().decode('utf-8').strip()
        if CYCLE.program != SETUP.program:
            CYCLE = Cycle(SETUP.program)
            CYCLE.register_stopfunc(insert_and_remove)
        if SETUP.stoptime is None:
            SETUP.stop()
        CYCLE.process_event(line)

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
                if ms in CYCLES:
                    ms = CYCLES._inner.index(ms)
                return program


def recv_serial(device):
    strline = device.readline().decode('utf-8').strip()
    print("Got %s" % (strline))
    return strline

def test_serial():
    ser = Serial("/dev/ttyAMA0", 115200)
    while True:
        if POLL_ARGS["comm"] == "stop":
            exit()
        line = ser.readline().decode('utf-8').strip()
        global CYCLE
        CYCLE.process_event(line)
        CYCLES.append(CYCLE)
        for c in CYCLES:
            print("motion -> %s" % (c))
        print('-'*10)

def main():
    """
    Main loop.
    """
    try:
        os.system('stty -echo')
        InputDeviceDispatcher(evdev.InputDevice(get_device(['WIT 122-UFS',])))
        ser = Serial("/dev/ttyAMA0", 115200)
        t = SerialThread(ser)
        t.daemon = True
        t.start()

        # SerialDispatcher(ser)
        loop()
    except KeyboardInterrupt:
        POLL_ARGS["comm"] = "stop"
        t.join()
        print('KeyboardInterrupt')
    finally:
        os.system('stty echo')
        print('Exiting...')

    exit(0)


if __name__ == "__main__":
    main()
