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

from json import loads
from .cycle import Cycle


class Cycles(object):
    """
    An object for processing a pile of Cycle objects.
    """
    def __init__(self, *args):
        self._inner = None
        if args is not None:
            self._inner = [arg for arg in args if isinstance(arg, Cycle)]

    def __iter__(self):
        for item in self._inner:
            yield item

    def __len__(self):
        return len(self._inner)

    def __getitem__(self, index):
        return self._inner[index]

    def __setitem__(self, index, value):
        self._inner[index] = value

    def __delitem__(self, index):
        self._inner.remove(self._inner[index])

    def append(self, cycle):
        """
        Add another cycle to the pile.
        """
        if self._inner is not None:
            self._inner.append(cycle)
        else:
            self._inner = list(cycle)

    def remove(self, cycle):
        """
        Remove cycle from the list.
        """
        self._inner.remove(cycle)

    def average_time(self):
        """
        Return the average .diff() of all items.
        """
        total = sum([item.diff().seconds
                     for item in self._inner if item.diff() is not None])
        return total / len(self)

    def bsons(self):
        """
        Return a SON object.
        """
        return [d.bsons() for d in self._inner]

    def jsons(self):
        """
        Return a JSON object.
        """
        jstr = '[{}]'.format(', '.join(jstr.jsons() for jstr in self._inner))
        return loads(jstr)

    @property
    def program_list(self):
        """
        List program names of all the cycles.
        """
        if self._inner is not None and len(self._inner) > 0:
            return [item.program for item in self._inner]
        else:
            return None
