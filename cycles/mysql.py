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
EARLIEST = None


def insert(cyc, config):
    """
    Insert cycle data into a MySQL DB.
    """
    global EARLIEST
    if EARLIEST is None:
        EARLIEST = latest_entry_time(config)

    time_ok = (EARLIEST is not None) and (cyc.starttime > EARLIEST)
    start_not_none = cyc.starttime is not None
    stop_not_none = cyc.stoptime is not None

    connection = pymysql.connect(host=config.dbhost,
                                 user=config.dbuser,
                                 password=config.dbpass,
                                 db=config.db,
                                 cursorclass=pymysql.cursors.DictCursor)
    if time_ok and start_not_none and stop_not_none:
        try:
            with connection.cursor() as cursor:
                sql = ("INSERT INTO `CUT_CYCLE_TIMES` "
                       "(`MACHNUM`, `PARTID`, `PROGRAM`, "
                       "`QTY`, `STARTTIME`, `STOPTIME`, `SETUP`) VALUES "
                       "(%s, %s, %s, %s, %s, %s, %s)")
                cursor.execute(sql, cyc.data_set())
            connection.commit()
        except:
            loglocal('EVERR', 'Failed to insert "{}"'.format(cyc), config)
        finally:
            connection.close()

    if not time_ok:
        log_error("Time is out of whack. {}".format(cyc.starttime), config)


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

    try:
        with connection.cursor() as cursor:
            sql = ("INSERT INTO `CUT_CYCLE_EVENTS` "
                   "(TS, EVENT, MACHINE) VALUES "
                   "(UTC_TIMESTAMP(), %s, %s)")
            cursor.execute(sql, (filtered_entry[0:1024], HOSTNAME,))
        connection.commit()
    except:
        loglocal('LOGERR', 'Failed to log "{}"'.format(entry), config)
    finally:
        connection.close()


def loglocal(tp, entry, config):
    with open(config.log_path, 'a+') as fh:
        msg = '{}: [{}]: {}\n'.format(datetime.now(), tp, entry)
        fh.writelines(msg)


def log_error(entry, config):
    if config.log_err:
        log(entry, config)

    loglocal('ERROR', entry, config)


def log_input(entry, config):
    if config.log_input:
        log(entry, config)

    loglocal('INPUT', entry, config)


def log_event(entry, config):
    if config.log_events:
        log(entry, config)

    loglocal('EVENT', entry, config)


def log_startup(entry, config):
    if log_startup:
        log(entry, config)

    loglocal('START', entry, config)


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


def latest_entry_time(config):
    connection = pymysql.connect(host=config.dbhost,
                                 user=config.dbuser,
                                 password=config.dbpass,
                                 db=config.db,
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            sql = ("SELECT MAX(STARTTIME) FROM CUT_CYCLE_TIMES")
            cursor.execute(sql)
            return cursor.fetchone()['MAX(STARTTIME)']
    except:
        log_error('Could not get latest date from db.', config)
    finally:
        connection.close()
