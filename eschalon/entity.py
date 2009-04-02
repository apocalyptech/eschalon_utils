#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Savefile Editor
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

import struct
from eschalonb1 import dirtable, entitytable
from eschalonb1.savefile import FirstItemLoadException

class Entity(object):
    """ A class to hold data about a particular entity on a map. """

    def __init__(self, savegame=True):
        """ A fresh object with no data. """

        self.savegame = savegame
        self.entid = -1
        self.x = -1
        self.y = -1
        self.direction = -1
        self.script = ''

        self.friendly = -1
        self.unknownc1 = -1
        self.health = -1
        self.unknownc2 = -1
        self.initial_inside = -1
        self.initial_outside = -1
        self.ent_zero1 = -1
        self.ent_zero2 = -1

    def replicate(self):
        newentity = Entity()

        # Simple Values
        newentity.savegame = self.savegame
        newentity.entid = self.entid
        newentity.x = self.x
        newentity.y = self.y
        newentity.direction = self.direction
        newentity.script = self.script
        newentity.friendly = self.friendly
        newentity.unknownc1 = self.unknownc1
        newentity.health = self.health
        newentity.unknownc2 = self.unknownc2
        newentity.initial_inside = self.initial_inside
        newentity.initial_outside = self.initial_outside
        newentity.ent_zero1 = self.ent_zero1
        newentity.ent_zero2 = self.ent_zero2

        # ... aaand return our new object
        return newentity

    def read(self, df):
        """ Given a file descriptor, read in the entity. """

        # We throw an exception because there seems to be an arbitrary
        # number of entities in the file, and no 'entity count' anywhere.
        # TODO: verify that the count isn't in the main map file.
        if (df.eof()):
            raise FirstItemLoadException('Reached EOF')

        # ... everything else
        self.entid = df.readuchar()
        self.x = df.readuchar()
        self.y = df.readuchar()
        self.direction = df.readuchar()
        self.script = df.readstr()
        if (self.savegame):
            self.friendly = df.readuchar()
            self.unknownc1 = df.readuchar()
            self.health = df.readint()
            self.unknownc2 = df.readuchar()
            self.initial_inside = df.readuchar()
            self.initial_outside = df.readuchar()
            self.ent_zero1 = df.readuchar()
            self.ent_zero2 = df.readuchar()

    def write(self, df):
        """ Write the entity to the file. """

        df.writeuchar(self.entid)
        df.writeuchar(self.x)
        df.writeuchar(self.y)
        df.writeuchar(self.direction)
        df.writestr(self.script)
        if (self.savegame):
            df.writeuchar(self.friendly)
            df.writeuchar(self.unknownc1)
            df.writeint(self.health)
            df.writeuchar(self.unknownc2)
            df.writeuchar(self.initial_inside)
            df.writeuchar(self.initial_outside)
            df.writeuchar(self.ent_zero1)
            df.writeuchar(self.ent_zero2)

    def tozero(self, x, y):
        """ Zeroes out the entity object.  Apart from x and y, which are passed in. """
        self.x = x
        self.y = y
        self.entid = 1
        self.direction = 1
        self.script = ''
        if (self.savegame):
            self.friendly = 0
            self.unknownc1 = 0
            self.health = 0
            self.unknownc2 = 0
            self.initial_inside = 0
            self.initial_outside = 0
            self.ent_zero1 = 0
            self.ent_zero2 = 0
            self.set_initial(x, y)

    def set_initial(self, x, y):
        """
        Set our "initial" parameters, given actual (x,y) coordinates.
        """
        squarenum = (y*100)+x
        self.initial_inside = squarenum % 256
        self.initial_outside = int(squarenum/256)

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        ret = []

        if (self.entid in entitytable):
            ret.append("\tEntity: %s" % (entitytable[self.entid].name))
        else:
            ret.append("\tEntity ID: %d" % (self.entid))
        ret.append("\tMap Location: (%d, %d)" % (self.x, self.y))
        if (self.direction in dirtable):
            ret.append("\tFacing %s" % (dirtable[self.direction]))
        else:
            ret.append("\tDirection ID: %d" % (self.direction))
        ret.append("\tScript: %s" % self.script)
        if (self.savegame):
            ret.append("\tFriendly: %d" % (self.friendly))
            ret.append("\tHealth: %d" % (self.health))
            ret.append("\tInitial Location (inside counter): %d" % self.initial_inside)
            ret.append("\tInitial Location (outside counter): %d" % self.initial_outside)
            if (unknowns):
                ret.append("\tUnknown value 1 (generally 1 or 2): %d" % self.unknownc1)
                ret.append("\tUnknown value 2 (generally 0 or 1): %d" % self.unknownc2)
                ret.append("\tUsually Zero (1): %d" % self.ent_zero1)
                ret.append("\tUsually Zero (2): %d" % self.ent_zero2)
        else:
            ret.append( "\t(No extra attributes - this is the base map definition file)")

        return "\n".join(ret)
