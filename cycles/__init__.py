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

__author__ = "K. C. Juntunen"
__copyright__ = "Copyright 2016, K. C. Juntunen"
__credits__ = ["K. C. Juntunen"]

__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "K. C. Juntunen"
__email__ = "juntunen.kc@gmail.com"
__status__ = "Development"

from .cycle import Cycle
from .machinesetup import MachineSetup
from .cycles import Cycles
from . import listen

__all__ = ["Cycle", "MachineSetup", "Cycles", "listen"]

# Logging format
LOGGING_FORMAT = '%(asctime)-15s:%(levelname)s:%(name)s:%(message)s'
CONSOLE_FORMAT = '%(levelname)s: %(message)s'
