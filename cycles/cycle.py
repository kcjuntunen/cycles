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
import socket
import time
import sched
from datetime import datetime
from collections import namedtuple
from json import loads, dumps
from bson import SON

HOSTNAME = socket.getfqdn().split()[0]


class Cycle(object):
    """
    A cycle record. The input can be '$'-separated items. The order should
    be 1) program, 2) job, 3) blank_qty, 4) partID.
    """
    def __init__(self, raw_string):
        """
        We only need a program name to start our Cycle object.
        """
        self._raw = raw_string
        self._setup = False
        self._program = self._raw
        self._partID = '0'
        self._job = 'Unknown'
        self._qty = '1'
        try:
            if '$' in self._raw:
                self._program, self._qty, self._partID = self._raw.split('$')
        except TypeError as te:
            self._raw = 'Bad input'

        self._starttime = None
        self._stoptime = None
        self._stopfunctions = None
        self._stopfuncsexeced = False
        self._lastUpdate = datetime.utcnow()
        self._wait = 0
        self._ignore = 5
        self._schedule = sched.scheduler(time.time, time.sleep)

    def __iter__(self):
        for i in [['display_name', self.display_name],
                  ['partID', self.partID],
                  ['program', self.program],
                  # ['job', self.job],
                  ['qty', self.qty],
                  ['start', self.starttime],
                  ['stop', self.stoptime],
                  ['setup', self.setup], ]:
            yield i

    def __eq__(self, rhs):
        if isinstance(rhs, str):
            return self.program == rhs
        else:
            return str(self) == str(rhs)

    def __str__(self):
        obj_contents = dict(self)
        return ', '.join(['{}: {}'.format(key, obj_contents[key])
                          for key in obj_contents])

    def bsons(self):
        """
        Returns a SON object. The idea is to insert directly into a
        NoSQL db.
        """
        bson_obj = SON()
        bson_obj.update(dict(self))
        return bson_obj

    def jsons(self):
        """
        Returns a JSON string of the object's data.
        """
        start, stop = None, None
        if self._starttime is not None:
            start = self.starttime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        if self._stoptime is not None:
            stop = self.stoptime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return dumps(dict(display_name=self.display_name, partID=self.partID,
                          program=self.program, qty=self.qty,
                          start=start, stop=stop, setup=self.setup))

    def data_set(self):
        """
        Returns a set of data that can be easily inserted into a traditional
        SQL db.
        """
        DataSet = namedtuple('DataSet', "machine partID program "
                             "qty starttime stoptime setup")
        ds = DataSet(HOSTNAME, self.partID, self.program, self.qty,
                     self.starttime, self.stoptime, self.setup, )
        return ds

    def process_event(self, event):
        """
        We will, perhaps, be receiving a JSON string from an Arduino.
        We need to store the time when we receive a start event, or a
        stop event.
        """
        json_obj = None
        try:
            json_obj = loads(event)
        except ValueError:
            # not json; we'll just pretend we didn't see that
            pass
        except TypeError:
            # not even str
            pass

        if json_obj is not None and "Event" in json_obj:
            if 'start' in json_obj["Event"]:
                self.start()
            if 'stop' in json_obj["Event"]:
                self.stop()
        else:
            pass

    def start(self):
        """
        Store a start time.
        """
        self._stopfuncsexeced = False
        if self.starttime is None:
            dt = datetime.utcnow()
            self._starttime = dt
            self._lastUpdate = dt
        self._stoptime = None

    def stop(self):
        """
        Store a stop time. Ignore if self._starttime isn't populated.
        """
        self._stopfuncsexeced = False
        if self._starttime is not None:
            dt = datetime.utcnow()
            self._stoptime = dt
            self._lastUpdate = dt

        # self.execute_stopfuncs()

    def execute_stopfuncs(self):
        if self._stopfunctions is not None:
            self._stopfuncsexeced = True
            for func in self._stopfunctions:
                func(self)
            self._stopfunctions = None

    def schedule_stopfuncs(self):
        if self._stopfunctions is not None:
            for func in self._stopfunctions:
                print("scheduling %s" % (func,))
                self._schedule.enterabs(time.time() + self._wait, 1, func,
                                        (self, ))
            self._schedule.run(blocking=False)

    def cancel_stopfuncs(self):
        for event in self._schedule.queue:
            print("Cancelling %s" % (event,))
            self._schedule.cancel(event)

    def register_stopfunc(self, func):
        """
        Functions to execute when data is complete.
        """
        # import pdb; pdb.set_trace()
        # self._schedule.enter(self._wait, 1, func, (self, ))
        if self._stopfunctions is None:
            self._stopfunctions = [func]
        else:
            self._stopfunctions.append(func)

    def diff(self):
        """
        Return a datetime.timedelta indicating the difference between
        the two times.
        """
        res = None
        if self.starttime is not None and self.stoptime is not None:
            res = self.stoptime - self.starttime
        return res

    @property
    def raw_string(self):
        """
        Return original string.
        """
        return self._raw

    @property
    def program(self):
        """
        Return program name.
        """
        return self._program

    @property
    def display_name(self):
        """
        Return a name for display.
        """
        return self.program

    @property
    def starttime(self):
        """
        Return start time.
        """
        return self._starttime

    @property
    def stoptime(self):
        """
        Return stop time.
        """
        return self._stoptime

    # @property
    # def job(self):
    #     """
    #     Return the job number collected upon instantiation.
    #     """
    #     return self._job

    @property
    def qty(self):
        """
        Return the qty received upon instantiation.
        """
        return int(self._qty, 10)

    @property
    def setup(self):
        """
        Is setup time?
        This looks to be revealing a design flaw.
        """
        return self._setup

    @property
    def partID(self):
        """
        Return the partID received upon instantiation.
        """
        return int(self._partID, 16)

    @property
    def LastUpdate(self):
        return self._lastUpdate
