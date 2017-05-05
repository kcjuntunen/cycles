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
                    'db serialport serialbaud wait scanners')


def config():
    st = os.stat('/etc/cycles.conf')
    if os.getuid() == st.st_uid:
        try:
            config_file = '/etc/cycles.conf'
            with open(config_file, 'r') as fh:
                config = configparser.ConfigParser()
                config.readfp(fh)
                CONFIG = Config(config.get('Database', 'host'),
                                config.get('Database', 'user'),
                                config.get('Database', 'pwd'),
                                config.get('Database', 'port'),
                                config.get('Database', 'db'),
                                # config.get('Serial', 'port'),
                                glob('/dev/tty[AU]*')[0],
                                config.get('Serial', 'baud'),
                                float(config.get('Serial', 'wait')),
                                config.get('Serial', 'scanners').split(';'),)
                return CONFIG
        except IndexError:
            print("Serial port not found.")
            exit(1)
        except Exception as e:
            print(e,)
            exit(1)
    else:
        raise PermissionError('Cannot access "%s"' % config_file)
