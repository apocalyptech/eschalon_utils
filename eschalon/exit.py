#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Book 1 Character Editor
# Copyright (C) 2008 CJ Kucera
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

class Exit:
    """ A class to hold data about a particular exit on a map. """

    def __init__(self):
        """ A fresh object with no data. """

        self.unknowni1 = -1
        self.mapid = ''
        self.number = ''    # apparently the coords of where to spawn on the new map, Y before X (and no delimiter?)
        self.unknowni2 = -1
        self.unknowni3 = -1
        self.unknowni4 = -1
        self.unknowni5 = -1
        self.unknowni6 = -1
        self.unknownh1 = -1
        self.script = ''
        self.unknowns1 = ''
        self.unknowns2 = ''
        self.unknowns3 = ''
        self.unknowns4 = ''
        self.unknowns5 = ''
        self.unknowns6 = ''
        self.unknowns7 = ''
        self.unknowns8 = ''

    def replicate(self):
        newexit = Exit()

        # Simple Values
        newexit.unknowni1 = self.unknowni1
        newexit.mapid = self.mapid
        newexit.number = self.number
        newexit.unknowni2 = self.unknowni2
        newexit.unknowni3 = self.unknowni3
        newexit.unknowni4 = self.unknowni4
        newexit.unknowni5 = self.unknowni5
        newexit.unknowni6 = self.unknowni6
        newexit.unknownh1 = self.unknownh1
        newexit.script = self.script
        newexit.unknowns1 = self.unknowns1
        newexit.unknowns2 = self.unknowns2
        newexit.unknowns3 = self.unknowns3
        newexit.unknowns4 = self.unknowns4
        newexit.unknowns5 = self.unknowns5
        newexit.unknowns6 = self.unknowns6
        newexit.unknowns7 = self.unknowns7
        newexit.unknowns8 = self.unknowns8

        # ... aaand return our new object
        return newexit

    def read(self, df):
        """ Given a file descriptor, read in the exit. """

        self.unknowni1 = df.readint()
        self.mapid = df.readstr()
        self.number = df.readstr()
        self.unknowni2 = df.readint()
        self.unknowni3 = df.readint()
        self.unknowni4 = df.readint()
        self.unknowni5 = df.readint()
        self.unknowni6 = df.readint()
        self.unknownh1 = df.readshort()
        self.script = df.readstr()
        self.unknowns1 = df.readstr()
        self.unknowns2 = df.readstr()
        self.unknowns3 = df.readstr()
        self.unknowns4 = df.readstr()
        self.unknowns5 = df.readstr()
        self.unknowns6 = df.readstr()
        self.unknowns7 = df.readstr()
        self.unknowns8 = df.readstr()

    def write(self, df):
        """ Write the exit to the file. """

        df.writeint(self.unknowni1)
        df.writestr(self.mapid)
        df.writestr(self.number)
        df.writeint(self.unknowni2)
        df.writeint(self.unknowni3)
        df.writeint(self.unknowni4)
        df.writeint(self.unknowni5)
        df.writeint(self.unknowni6)
        df.writeshort(self.unknownh1)
        df.writestr(self.script)
        df.writestr(self.unknowns1)
        df.writestr(self.unknowns2)
        df.writestr(self.unknowns3)
        df.writestr(self.unknowns4)
        df.writestr(self.unknowns5)
        df.writestr(self.unknowns6)
        df.writestr(self.unknowns7)
        df.writestr(self.unknowns8)

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        print "Map ID: %s" % self.mapid
        print "Script: %s" % self.script
        if (unknowns):
            print "A Number: %s" % self.number
            print "Unknown Integer 1: %d" % self.unknowni1
            print "Unknown Integer 2: %d" % self.unknowni2
            print "Unknown Integer 3: %d" % self.unknowni3
            print "Unknown Integer 4: %d" % self.unknowni4
            print "Unknown Integer 5: %d" % self.unknowni5
            print "Unknown Integer 6: %d" % self.unknowni6
            print "Unknown Short 1: %d" % self.unknownh1
            print "Unknown String 1 (usually empty): %s" % self.unknowns1
            print "Unknown String 2 (usually empty): %s" % self.unknowns2
            print "Unknown String 3 (usually empty): %s" % self.unknowns3
            print "Unknown String 4 (usually empty): %s" % self.unknowns4
            print "Unknown String 5 (usually empty): %s" % self.unknowns5
            print "Unknown String 6 (usually empty): %s" % self.unknowns6
            print "Unknown String 7 (usually empty): %s" % self.unknowns7
            print "Unknown String 8 (usually empty): %s" % self.unknowns8
