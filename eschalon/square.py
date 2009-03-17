#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Character Editor
# Copyright (C) 2008, 2009 CJ Kucera
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

class Square(object):
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
        self.entity = None

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
        
        # Objects
        if (self.entity is not None):
            newsquare.entity = self.entity.replicate()

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

    def delscript(self, script):
        """
        Remove a script.
        """
        self.scripts.remove(script)

    def addentity(self, entity):
        """
        Add an entity to our entity list.  Just an internal construct which isn't actually
        stored on disk.
        """
        self.entity = entity

    def delentity(self):
        """
        Remove our entity.  No matter if we don't have one.
        """
        self.entity = None

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        ret = []
        ret.append("    Wall Flag: %d" % self.wall)
        ret.append("    Floor Image: %d" % self.floorimg)
        ret.append("    Decal Image: %d" % self.decalimg)
        ret.append("    Wall Image: %d" % self.wallimg)
        ret.append("    Wall Decal Image: %d" % self.walldecalimg)
        ret.append("    Script ID: %d" % self.scriptid)
        if (unknowns):
            ret.append("    Unknown 5: %d" % self.unknown5)

        # Display any entities we may have
        if (self.entity is not None):
            ret.append('')
            ret.append("  Associated Entity:")
            ret.append(self.entity.display(unknowns))
            ret.append('')

        # Display any scripts we may have
        for script in self.scripts:
            ret.append('')
            ret.append("  Associated Script:")
            ret.append(script.display(unknowns))
        ret.append('')

        # Return
        return "\n".join(ret)
