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
from threading import Thread, Event
from datetime import datetime
import sys
import evdev
import urllib3
from cycles import config
from cycles import mysql
from cycles.cycle import Cycle
from cycles.cycles import Cycles
from cycles.machinesetup import MachineSetup


def connection_up(server):
    timeout = urllib3.Timeout(connect=5.0, read=5.0)
    http = urllib3.PoolManager(timeout=timeout)
    try:
        http.request('GET', server)
    except:
        with open('/var/log/cycles_fail.log', 'a+') as fh:
            msg = '%s: Cannot connect to server.\n' % datetime.now()
            fh.writelines(msg)
            print(msg)
        return False
    return True


try:
    CONFIG = config.config()
    # if not connection_up(CONFIG.dbhost):
    #     exit(-1)

    msg = ('Ignoring cycles shorter than {} seconds,'
           'longer than {} minutes; '
           'gaps shorter than {} seconds'.format(CONFIG.too_short,
                                                 CONFIG.too_long / 60,
                                                 CONFIG.wait,))
    mysql.log_startup(msg, CONFIG)
except Exception as e:
    print('%s: Failure loading config. (%s)' % (datetime.utcnow(), e,))

ser = Serial(CONFIG.serialport, CONFIG.serialbaud, timeout=1)

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
        try:
            return self.device.read()
        except TypeError as ex:
            mysql.log_error('Barcode scanner not found.', CONFIG)

    def writable(self):
        return False

    def handle_read(self):
        global CYCLES
        global SETUP
        global SetupMode
        global CurrentProg
        reading = recv_scanner(self.device)
        mysql.log_input(reading, CONFIG)
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
    try:
        diff = 0

        if cyc.diff() is not None:
            diff = cyc.diff().seconds

        too_short = diff < CONFIG.too_short
        too_long = diff > CONFIG.too_long

        if not too_short and not too_long:
            msg = "Inserting (%s)" % (cyc, )
            mysql.log_event(msg, CONFIG)
            mysql.insert(cyc, CONFIG)
            CYCLES.remove(cyc)
            cyc._starttime = None
            cyc._stoptime = None

        if too_short:
            msg = "Cycle < %s seconds. Ignoring (%s)" % (CONFIG.too_short,
                                                         cyc,)
            mysql.log_event(msg, CONFIG)
            CYCLES.remove(cyc)
            cyc._starttime = None
            cyc._stoptime = None

        if too_long:
            msg = "Cycle > %s minutes. Ignoring (%s)" % (CONFIG.too_long / 60,
                                                         cyc,)
            mysql.log_event(msg, CONFIG)
            CYCLES.remove(cyc)
            cyc._starttime = None
            cyc._stoptime = None
    except Exception as e:
        msg = 'Failed insert. (%s)' % (e,)
        mysql.log_error(msg, CONFIG)


class SerialThread(Thread):
    def __init__(self, ser):
        super(SerialThread, self).__init__()
        self._stop_event = Event()
        self.ser = ser

    def run(self):
        serial_loop(self.ser)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def serial_loop(ser):
    # print('serial started')
    global CYCLE
    global CurrentProg
    global newStart
    while True:
        if POLL_ARGS["comm"] == "stop":
            break
        try:
            line = ser.read(1).decode('utf8')
            line += ser.readline().decode('utf8').strip()
        except:
            mysql.log_error('Failed utf8 decode.', CONFIG)

        if line != '':
            mysql.log_input(line, CONFIG)
        else:
            continue

        if "start" in line:
            try:
                dt = datetime.utcnow()
                if ((dt - CYCLE.LastUpdate).seconds < CONFIG.wait and
                        CYCLE.stoptime is not None):
                    newStart = True
                    continue
                if (CYCLE._stopfuncsexeced is True or
                        CYCLE.starttime is None):
                    mysql.log_event('Creating new cycle @ %s' % (dt,), CONFIG)
                    newStart = False
                    CYCLE = Cycle(CurrentProg)
                    CYCLE._stopfuncsexeced = False
                    CYCLE._ignore = CONFIG.too_short
                    # CYCLE.process_event(line)
                    CYCLE.start()
                    CYCLE.register_stopfunc(insert_and_remove)
                    if CYCLE not in CYCLES:
                        CYCLES.append(CYCLE)
            except Exception as e:
                lineno = sys.exc_info()[-1].tb_lineno
                mysql.log_error('Failed start at line %s. (%s)' % (lineno, e,),
                                CONFIG)
        if "stop" in line:
            try:
                # CYCLE.process_event(line)
                newStart = False
                CYCLE.stop()
            except Exception as e:
                lineno = sys.exc_info()[-1].tb_lineno
                mysql.log_error('Failed stop at line %s. (%s)' % (lineno, e,),
                                CONFIG)


class ExpireThread(Thread):
    def __init__(self):
        super(ExpireThread, self).__init__()
        self._stop_event = Event()

    def run(self):
        expire_cycle()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def expire_cycle():
    global CYCLE
    global newStart
    while True:
        if POLL_ARGS["comm"] == "stop":
            break
        try:
            cyc = CYCLE
            if cyc is not None:
                if (cyc.starttime is not None and
                        cyc.stoptime is not None):
                    dt = datetime.utcnow()
                    if (not newStart and
                            abs(dt - cyc.LastUpdate).seconds > CONFIG.wait):
                        cyc.execute_stopfuncs()
        except Exception as e:
            lineno = sys.exc_info()[-1].tb_lineno
            mysql.log_error('Failed expire at line %s. (%s)' % (lineno, e,),
                            CONFIG)


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
                mysql.log_startup('Found "%s"' % (name,), CONFIG)
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
        except TypeError as ex:
            mysql.log_error('Barcode scanner not found.', CONFIG)
            exit(-1)

        t = SerialThread(ser)
        t.start()

        et = ExpireThread()
        et.start()

        mysql.log_startup('Monitor started at %s.' % (datetime.utcnow(),),
                          CONFIG)
        loop(timeout=5.0)
    except KeyboardInterrupt:
        POLL_ARGS["comm"] = "stop"
        t.stop()
        et.stop()
        t.join()
        et.join()
        if CYCLE.starttime is not None and CYCLE.stoptime is not None:
            CYCLE.execute_stopfuncs()
        mysql.log_startup('Keyboard Interrupt', CONFIG)
    finally:
        mysql.log_startup('Exiting', CONFIG)

    exit(0)


if __name__ == "__main__":
    main()
