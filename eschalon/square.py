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

from eschalon import constants as c

class Square(object):
    """ A class to hold data about a particular square on a map. """

    def __init__(self, x, y):
        """ A fresh object with no data. """

        self.x = x
        self.y = y

        self.wall = -1
        self.floorimg = -1
        self.decalimg = -1
        self.wallimg = -1
        self.unknown5 = -1
        self.walldecalimg = -1
        self.scriptid = -1

        self.scripts = []
        self.entity = None
        self.savegame = False

    def replicate(self):
        newsquare = Square(self.x, self.y)

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

    def equals(self, square):
        """
        Compare ourselves to another square object.  We're just
        checking if our values are the same, NOT if we're *actually*
        the same object.  Returns true for equality, false for inequality.
        """
        # TODO: We need to check entity and script indexes here, too.
        return (self.x == square.x and
                self.y == square.y and
                self.wall == square.wall and
                self.floorimg == square.floorimg and
                self.decalimg == square.decalimg and
                self.wallimg == square.wallimg and
                self.unknown5 == square.unknown5 and
                self.walldecalimg == square.walldecalimg and
                self.scriptid == square.scriptid and
                self.entity_equals(square.entity) and
                self.scripts_equal(square.scripts))

    def entity_equals(self, entity):
        """
        Compare the contents of our entity to the contents of the
        given entity.
        """
        if (self.entity is None):
            return (entity is None)
        else:
            if (entity is None):
                return False
            else:
                return self.entity.equals(entity)

    def scripts_equal(self, scripts):
        """
        Compare the contents of our scripts to the contents of the
        given scripts.
        """
        if (len(self.scripts) != len(scripts)):
            return False
        for (myscript, compscript) in zip(self.scripts, scripts):
            if (not myscript.equals(compscript)):
                return False
        return True

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
        if (self.scriptid in c.objecttypetable):
            ret.append("    Object Type: %s" % c.objecttypetable[self.scriptid])
        else:
            ret.append("    Object Type: %d" % self.scriptid)
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
            ret.append("  Associated Object:")
            ret.append(script.display(unknowns))
        ret.append('')

        # Return
        return "\n".join(ret)
    
    @staticmethod
    def new(book, x, y):
        """
        Static method to initialize the correct object
        """
        if book == 1:
            return B1Square(x, y)
        else:
            return B2Square(x, y)

class B1Square(Square):
    """
    Square structure for Book 1
    """

    book = 1

    def __init__(self, x, y):
        super(B1Square, self).__init__(x, y)

        # Book 1 specific vars
        self.unknown5 = -1
        # This var is *probably* actually part of the wall ID, like in book 2

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

class B2Square(Square):
    """
    Square structure for Book 2
    """

    book = 2

    def __init__(self, x, y):
        super(B2Square, self).__init__(x, y)

        # Book 2 specific vars
        self.unknowni1 = -1

    def read(self, df):
        """ Given a file descriptor, read in the square. """

        self.wall = df.readuchar()
        self.floorimg = df.readuchar()
        self.decalimg = df.readuchar()
        self.wallimg = df.readshort()
        self.walldecalimg = df.readuchar()
        self.scriptid = df.readuchar()
        if self.savegame:
            self.unknowni1 = df.readint()

    def write(self, df):
        """ Write the square to the file. """

        df.writeuchar(self.wall)
        df.writeuchar(self.floorimg)
        df.writeuchar(self.decalimg)
        df.writeshort(self.wallimg)
        df.writeuchar(self.walldecalimg)
        df.writeuchar(self.scriptid)
        if self.savegame:
            df.writeint(self.unknowni1)
