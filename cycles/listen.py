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
from asyncore import file_dispatcher, loop
from serial import Serial
from threading import Thread
from datetime import datetime
import evdev
from cycles import config
from cycles import mysql
from cycles.cycle import Cycle
from cycles.cycles import Cycles
from cycles.machinesetup import MachineSetup

CONFIG = config.config()
mysql.log("Ignoring cycles less than %s seconds, and gaps shorter than %s "
          "seconds." % (CONFIG.ignore, CONFIG.wait,), CONFIG)
try:
    CurrentProg
except NameError:
    CurrentProg = 'No program'

SETUP = MachineSetup(CurrentProg)
SetupMode = False
SETUP.stop()

CYCLE = Cycle(SETUP.raw_string)
CYCLES = Cycles(SETUP)

newStart = False
lastStop = datetime.utcnow()

POLL_ARGS = {"comm": "go", }
SCANCODES = {
    0x02: '1', 0x03: '2', 0x04: '3', 0x05: '4', 0x06: '5',
    0x07: '6', 0x08: '7', 0x09: '8', 0x0A: '9', 0x0B: '0',

    0x0C: '-',

    0x10: 'Q', 0x11: 'W', 0x12: 'E', 0x13: 'R', 0x14: 'T',
    0x15: 'Y', 0x16: 'U', 0x17: 'I', 0x18: 'O', 0x19: 'P',

    # 28: 'CRLF',

    0x1E: 'A', 0x1F: 'S', 0x20: 'D', 0x21: 'F', 0x22: 'G',
    0x23: 'H', 0x24: 'J', 0x25: 'K', 0x26: 'L', 0x27: ';',

    # 0x2A: 'LSHIFT',

    0x2C: 'Z', 0x2D: 'X', 0x2E: 'C', 0x2F: 'V', 0x30: 'B',
    0x31: 'N', 0x32: 'M', 0x33: ',', 0x34: '.', 0x35: '/',

    # 0x36: 'RSHIFT',
}

SHIFT_SCANCODES = {
    0x02: '!', 0x03: '@', 0x04: '#', 0x05: '$', 0x06: '%',
    0x07: '^', 0x08: '&', 0x09: '*', 0x0A: '(', 0x0B: ')',

    0x0C: '_',

    0x10: 'Q', 0x11: 'W', 0x12: 'E', 0x13: 'R', 0x14: 'T',
    0x15: 'Y', 0x16: 'U', 0x17: 'I', 0x18: 'O', 0x19: 'P',

    0x1E: 'A', 0x1F: 'S', 0x20: 'D', 0x21: 'F', 0x22: 'G',
    0x23: 'H', 0x24: 'J', 0x25: 'K', 0x26: 'L', 0x27: ';',

    0x2C: 'Z', 0x2D: 'X', 0x2E: 'C', 0x2F: 'V', 0x30: 'B',
    0x31: 'N', 0x32: 'M', 0x33: '<', 0x34: '>', 0x35: '?',
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
        global CYCLES
        global SETUP
        global SetupMode
        global CurrentProg
        reading = recv_scanner(self.device)
        print(reading)
        mysql.log(reading, CONFIG)
        if reading == "%EOS%" and SetupMode:
            SetupMode = False
            SETUP.stop()
            SETUP.execute_stopfuncs()
        elif '%' in reading:
            pass
        else:
            if CYCLE.starttime is not None and CYCLE.stoptime is not None:
                CYCLE.execute_stopfuncs()
            SetupMode = True
            CurrentProg = reading
            SETUP = MachineSetup(reading)
            SETUP._wait = 0
            CYCLES = Cycles(SETUP)
            SETUP.register_stopfunc(insert_and_remove)

    # def handle_read2(self):
    #     # print("handle scanner")
    #     global CYCLES
    #     global SETUP
    #     SETUP = MachineSetup(recv_scanner(self.device))
    #     CYCLES = Cycles(SETUP)
    #     SETUP.register_stopfunc(insert_and_remove)
    #     # print("scan -> %s" % (CYCLES))


def insert_and_remove(cyc):
    diff = cyc.diff().seconds
    if diff is None:
        diff = 0
    if diff > CONFIG.ignore:
        msg = "Inserting %s" % (cyc, )
        print(msg)
        mysql.log(msg, CONFIG)
        mysql.insert(cyc, CONFIG)
        CYCLES.remove(cyc)
        cyc._starttime = None
        cyc._stoptime = None
        cyc = Cycle(CurrentProg)
        cyc._ignore = CONFIG.ignore
    else:
        msg = "Cycle too short. Ignoring (%s)" % (cyc,)
        print(msg)
        mysql.log(msg, CONFIG)
        CYCLES.remove(cyc)
        cyc._starttime = None
        cyc._stoptime = None
        cyc = Cycle(CurrentProg)
        cyc._ignore = CONFIG.ignore


class SerialThread(Thread):
    def __init__(self, ser):
        Thread.__init__(self)
        self.ser = ser

    def run(self):
        serial_loop(self.ser)


def serial_loop(ser):
    # print('serial started')
    global CYCLE
    global CurrentProg
    global lastStop
    global newStart
    while True:
        if POLL_ARGS["comm"] == "stop":
            exit(0)
        line = ser.readline().decode('utf-8').strip()
        print('%s: %s' % (datetime.utcnow(), line,))
        mysql.log(line, CONFIG)

        if "start" in line:
            dt = datetime.utcnow()
            if (dt - lastStop).seconds < CONFIG.wait:
                newStart = True
                pass
            else:
                newStart = False
                CYCLE.execute_stopfuncs()
                CYCLE = Cycle(CurrentProg)
                CYCLE._ignore = CONFIG.ignore
                CYCLE.process_event(line)
                CYCLE.register_stopfunc(insert_and_remove)
        if "stop" in line:
            CYCLE.process_event(line)
            lastStop = datetime.utcnow()
            newStart = False


class ExpireThread(Thread):
    def run(self):
        expire_cycle()


def expire_cycle():
    global lastStop
    global CYCLE
    global newStart
    while True:
        if CYCLE.starttime is not None and CYCLE.stoptime is not None:
            dt = datetime.utcnow()
            if not newStart and (dt - lastStop).seconds > CONFIG.wait:
                CYCLE.execute_stopfuncs()
                CYCLE._ignore = CONFIG.ignore


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
                mysql.log('Found "%s"' % (name,), CONFIG)
                return dev.fn


def recv_scanner(device):
    """
    Parse the huge load of stuff that rolls in from the scanner.
    """
    program = ''
    shift = False
    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            data = evdev.categorize(event)
            if data.scancode == 0x2A:
                shift = data.keystate == 1
            if data.keystate == 1 and data.scancode != 28:
                if shift:
                    keypress = (SHIFT_SCANCODES.get(data.scancode) or '')
                    program += keypress
                else:
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


# def test_serial():
    # ser = Serial("/dev/ttyAMA0", 115200)
    # while True:
    #     if POLL_ARGS["comm"] == "stop":
    #         exit()
    #     line = ser.readline().decode('utf-8').strip()
    #     global CYCLE
    #     CYCLE.process_event(line)
    #     CYCLES.append(CYCLE)
    #     for c in CYCLES:
    #         print("motion -> %s" % (c))
    #     print('-'*10)


def main():
    """
    Main loop.
    """
    try:
        try:
            InputDeviceDispatcher(evdev.InputDevice(
                get_device(CONFIG.scanners)))
        except Exception as ex:
            print(ex)
            exit(-1)

        ser = Serial(CONFIG.serialport, CONFIG.serialbaud)
        t = SerialThread(ser)
        t.daemon = True
        t.start()

        et = ExpireThread()
        et.daemon = True
        et.start()

        mysql.log('Monitor started', CONFIG)
        loop()
    except KeyboardInterrupt:
        POLL_ARGS["comm"] = "stop"
        t.join()
        if CYCLE.starttime is not None and CYCLE.stoptime is not None:
            CYCLE.execute_stopfuncs()
        mysql.log('Keyboard Interrupt', CONFIG)
        print('KeyboardInterrupt')
    finally:
        mysql.log('Exiting', CONFIG)
        print('Exiting...')

    exit(0)


if __name__ == "__main__":
    main()
