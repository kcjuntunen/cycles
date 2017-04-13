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

import pymysql.cursors


def insert(cyc, config):
    connection = pymysql.connect(host=config.dbhost,
                                 user=config.dbuser,
                                 password=config.dbpass,
                                 db=config.db,
                                 cursorclass=pymysql.cursors.DictCursor)
    # print("%s.%s.%s" % (CONFIG.dbhost, CONFIG.db, CONFIG.collection))
    if cyc.stoptime is not None and cyc.starttime is not None:
        try:
            with connection.cursor() as cursor:
                sql = ("INSERT INTO `CUT_CYCLES_TIMES` "
                       "(`MACHNUM`, `PARTID`, `PROGRAM`, `JOB`, "
                       "`QTY`, `STARTTIME`, `STOPTIME`, `SETUP`) VALUES "
                       "(%s, %s, %s, %s, %s, %s, %s, %s)")
                cursor.execute(sql, cyc.data_set())
            connection.commit()
        finally:
            connection.close()
