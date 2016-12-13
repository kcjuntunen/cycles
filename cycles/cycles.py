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


class Cycles(object):
    """
    An object for processing a pile of Cycle objects.
    """
    def __init__(self, *args):
        self._inner = None
        if args is not None:
            self._inner = list(args)

    def __iter__(self):
        for item in self._inner:
            yield item

    def __len__(self):
        return len(self._inner)

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
                     for item in self._inner])
        return total / len(self)

    @property
    def program_list(self):
        """
        List program names of all the cycles.
        """
        if self._inner is not None and len(self._inner) > 0:
            return [item.program for item in self._inner]
        else:
            return None
