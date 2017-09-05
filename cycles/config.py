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
import configparser
from collections import namedtuple
from glob import glob

Config = namedtuple('Config', 'dbhost dbuser dbpass dbport '
                    'db serialport serialbaud scanners wait '
                    'too_short too_long log_path')


def config():
    st = os.stat('/etc/cycles.conf')
    if os.getuid() == st.st_uid:
        try:
            config_file = '/etc/cycles.conf'
            with open(config_file, 'r') as fh:
                config = configparser.ConfigParser()
                config.readfp(fh)

                sections = config.sections()
                # Defaults
                wait = 10
                too_short = 7.55
                too_long = 1800
                port = glob('/dev/tty[AU]*')[0]
                baud = 115200
                log_path = '/var/log/cycles_fail.log'

                if 'Limits' in sections:
                    itms = [i[0] for i in config.items('Limits')]
                    if 'wait' in itms:
                        wait = config.getfloat('Limits', 'wait')
                    if 'short' in itms:
                        too_short = config.getfloat('Limits', 'short')
                    if 'long' in itms:
                        too_long = config.getfloat('Limits', 'long')

                if 'Serial' in sections:
                    itms = [i[0] for i in config.items('Serial')]
                    if 'port' in itms:
                        port = config.get('Serial', 'port')
                    if 'baud' in itms:
                        baud = config.get('Serial', 'baud')

                if 'Log' in sections:
                    itms = [i[0] for i in config.items('Log')]
                    if 'path' in itms:
                        log_path = config.get('Log', 'path')

                CONFIG = Config(config.get('Database', 'host'),
                                config.get('Database', 'user'),
                                config.get('Database', 'pwd'),
                                config.get('Database', 'port'),
                                config.get('Database', 'db'),
                                port,
                                baud,
                                config.get('Serial', 'scanners').split(';'),
                                wait,
                                too_short,
                                too_long,
                                log_path,)

                return CONFIG
        except IndexError:
            print("Serial port not found.")
            exit(1)
        except Exception as e:
            print(e,)
            exit(1)
    else:
        raise PermissionError('Cannot access "%s"' % config_file)
