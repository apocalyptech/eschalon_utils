#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
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
        self.decalimg = -1
        self.wallimg = -1
        self.unknown5 = -1
        self.walldecalimg = -1
        self.scriptid = -1

        self.scripts = []

    def replicate(self):
        newsquare = Square()

        # Simple Values
        newsquare.wall = self.wall
        newsquare.floorimg = self.floorimg
        newsquare.decalimg = self.decalimg
        newsquare.wallimg = self.wallimg
        newsquare.unknown5 = self.unknown5
        newsquare.walldecalimg = self.walldecalimg
        newsquare.scriptid = self.scriptid

        # Arrays
        for script in self.scripts:
            newsquare.scripts.append(script.replicate())

        # ... aaand return our new object
        return newsquare

    def read(self, df):
        """ Given a file descriptor, read in the square. """

        self.wall = df.readuchar()
        self.floorimg = df.readuchar()
        self.decalimg = df.readuchar()
        self.wallimg = df.readuchar()
        self.unknown5 = df.readuchar()
        self.walldecalimg = df.readuchar()
        self.scriptid = df.readuchar()

    def write(self, df):
        """ Write the square to the file. """

        df.writeuchar(self.wall)
        df.writeuchar(self.floorimg)
        df.writeuchar(self.decalimg)
        df.writeuchar(self.wallimg)
        df.writeuchar(self.unknown5)
        df.writeuchar(self.walldecalimg)
        df.writeuchar(self.scriptid)

    def hasdata(self):
        """ Do we have something other than zeroes? """
        return (self.wall != 0 or self.floorimg != 0 or
                self.decalimg != 0 or self.wallimg != 0 or
                self.unknown5 != 0 or self.walldecalimg != 0 or
                self.scriptid != 0)
    
    def addscript(self, script):
        """
        Add a script to our script list.  Just an internal construct which isn't actually
        stored on disk.
        """
        self.scripts.append(script)

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        print "    Wall Flag: %d" % self.wall
        print "    Floor Image: %d" % self.floorimg
        print "    Decal Image: %d" % self.decalimg
        print "    Wall Image: %d" % self.wallimg
        print "    Wall Decal Image: %d" % self.walldecalimg
        print "    Script ID: %d" % self.scriptid
        if (unknowns):
            print "    Unknown 5: %d" % self.unknown5
