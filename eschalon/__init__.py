#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2017 CJ Kucera, Elliot Kendall, Eitan Adler
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging

import verboselogs

try:
    from gi import pygtkcompat
    pygtkcompat.enable()
    pygtkcompat.enable_gtk(version='3.0')
except ImportError:
    pass

verboselogs.install()

LOG = logging.getLogger(__name__)


# If app_name ever changes, we should update preferences/windows_prefsfile
# to provide an upgrade path
app_name = 'Eschalon Savefile Editor'
version = '1.0.3rc0'
url = 'http://apocalyptech.com/eschalon/'
authors = ['Main Code - CJ Kucera',
           'Additional Code / Ideas - WR Goerlich',
           'Book III / OS X Code - Elliot Kendall', '',
           'Some Icons by Axialis Team', 'see http://www.axialis.com/free/icons/']

__all__ = ['app_name', 'version', 'url', 'authors'
           'Savefile', 'Item', 'B1Unknowns', 'B2Unknowns',
           'Character', 'MainGUI', 'LoadException',
           'Tile', 'Tilecontent', 'Undo',
           'constants']
