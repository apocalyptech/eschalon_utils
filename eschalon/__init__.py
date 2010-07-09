#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2010 CJ Kucera
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

# If app_name ever changes, we should update preferences/windows_prefsfile
# to provide an upgrade path
app_name = 'Eschalon Savefile Editor'
version = '0.6.3'
url = 'http://apocalyptech.com/eschalon/'
authors = ['Main Code - CJ Kucera', 'Additional Code / Ideas - WR Goerlich', '', 'Some Icons by Axialis Team', 'see http://www.axialis.com/free/icons/']

__all__ = [ 'app_name', 'version', 'url', 'authors'
        'Savefile', 'Item', 'B1Unknowns', 'B2Unknowns',
        'Character', 'MainGUI', 'LoadException',
        'Square', 'Mapscript', 'Undo',
        'constants' ]

from eschalon.constantsb1 import B1Constants
from eschalon.constantsb2 import B2Constants

class Constants:
    """
    A class to hold our constants, depending on what book we're
    currently working in.  I suppose really this should just modify
    a global var and set it to B1Constants or B2Constants, but
    I'll just leave it this way for now.
    """

    def __init__(self, book=1):
        self.groups = {
                1: B1Constants,
                2: B2Constants
            }
        self.book = None
        self.switch_to_book(book)

    def switch_to_book(self, book):
        if book != self.book:
            #print "Switching to Book %d Constants" % (book)
            # First clear out the old constants
            if self.book:
                for (key, val) in self.groups[self.book].__dict__.items():
                    if key[0] != '_':
                        del(self.__dict__[key])
            # ... and now load in the new ones
            for (key, val) in self.groups[book].__dict__.items():
                if key[0] != '_':
                    self.__dict__[key] = val
            self.book = book

constants = Constants()
