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

from datetime import datetime
import pymysql.cursors
import socket


HOSTNAME = socket.getfqdn().split()[0]


def insert(cyc, config):
    """
    Insert cycle data into a MySQL DB.
    """
    connection = pymysql.connect(host=config.dbhost,
                                 user=config.dbuser,
                                 password=config.dbpass,
                                 db=config.db,
                                 cursorclass=pymysql.cursors.DictCursor)
    print(cyc)
    if cyc.stoptime is not None and cyc.starttime is not None:
        try:
            with connection.cursor() as cursor:
                sql = ("INSERT INTO `CUT_CYCLE_TIMES` "
                       "(`MACHNUM`, `PARTID`, `PROGRAM`, "
                       "`QTY`, `STARTTIME`, `STOPTIME`, `SETUP`) VALUES "
                       "(%s, %s, %s, %s, %s, %s, %s)")
                cursor.execute(sql, cyc.data_set())
            connection.commit()
        except:
            with open(config.log_path, 'a+') as fh:
                msg = '%s: Failed to log cycle: [%s]\n' % (datetime.now(), cyc, )
                fh.writelines(msg)
                print(msg)
        finally:
            connection.close()


def log(entry, config):
    """
    Insert log data into MySQL DB.
    """
    connection = pymysql.connect(host=config.dbhost,
                                 user=config.dbuser,
                                 password=config.dbpass,
                                 db=config.db,
                                 cursorclass=pymysql.cursors.DictCursor)
    filtered_entry = ''.join(c for c in str(entry) if c.isprintable())
    print(entry)
    try:
        with connection.cursor() as cursor:
            sql = ("INSERT INTO `CUT_CYCLE_EVENTS` "
                   "(TS, EVENT, MACHINE) VALUES "
                   "(UTC_TIMESTAMP(), %s, %s)")
            cursor.execute(sql, (filtered_entry[0:1024], HOSTNAME,))
        connection.commit()
    except:
        with open(config.log_path, 'a+') as fh:
            msg = '%s: Failed to log event: [%s]\n' % (datetime.now(), entry, )
            fh.writelines(msg)
            print(msg)
    finally:
        connection.close()


def log_err(entry, config):
    """
    Insert log data into MySQL DB.
    """
    connection = pymysql.connect(host=config.dbhost,
                                 user=config.dbuser,
                                 password=config.dbpass,
                                 db=config.db,
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            sql = ("INSERT INTO `GEN_ERRORS` "
                   "(`ERRDATE`, `ERRUSER`, `ERRNUM`, `ERRMSG`, "
                   "`ERROBJ`, `ERRAPP`) VALUES "
                   "(%s, %s, %s, %s, %s, %s)")
            cursor.execute(sql, entry)
        connection.commit()
    finally:
        connection.close()
