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

class Square:
    """ A class to hold data about a particular square on a map. """

    def __init__(self):
        """ A fresh object with no data. """

        self.wall = -1
        self.floorimg = -1
        self.unknown3 = -1
        self.wallimg = -1
        self.unknown5 = -1
        self.unknown6 = -1
        self.unknown7 = -1

    def replicate(self):
        newsquare = Square()

        # Simple Values
        newsquare.wall = self.wall
        newsquare.floorimg = self.floorimg
        newsquare.unknown3 = self.unknown3
        newsquare.wallimg = self.wallimg
        newsquare.unknown5 = self.unknown5
        newsquare.unknown6 = self.unknown6
        newsquare.unknown7 = self.unknown7

        # ... aaand return our new object
        return newsquare

    def read(self, df):
        """ Given a file descriptor, read in the square. """

        self.wall = df.readchar()
        self.floorimg = df.readchar()
        self.unknown3 = df.readchar()
        self.wallimg = df.readchar()
        self.unknown5 = df.readchar()
        self.unknown6 = df.readchar()
        self.unknown7 = df.readchar()

    def write(self, df):
        """ Write the square to the file. """

        df.writechar(self.wall)
        df.writechar(self.floorimg)
        df.writechar(self.unknown3)
        df.writechar(self.wallimg)
        df.writechar(self.unknown5)
        df.writechar(self.unknown6)
        df.writechar(self.unknown7)

    def hasdata(self):
        """ Do we have something other than zeroes? """
        return (self.wall != 0 or self.floorimg != 0 or
                self.unknown3 != 0 or self.wallimg != 0 or
                self.unknown5 != 0 or self.unknown6 != 0 or
                self.unknown7 != 0)

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        print "    Wall Flag: %d" % self.wall
        print "    Floor Image: %d" % self.floorimg
        print "    Wall Image: %d" % self.wallimg
        if (unknowns):
            print "    Unknown 3: %d" % self.unknown3
            print "    Unknown 5: %d" % self.unknown5
            print "    Unknown 6: %d" % self.unknown6
            print "    Unknown 7: %d" % self.unknown7
