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

import struct
from eschalon import constants as c
from eschalon.savefile import FirstItemLoadException

class Entity(object):
    """ A class to hold data about a particular entity on a map. """

    def __init__(self, savegame=True):
        """ A fresh object with no data. """

        self.savegame = savegame
        self.entid = -1
        self.x = -1
        self.y = -1
        self.direction = -1
        self.entscript = ''

        self.friendly = -1
        self.unknownc1 = -1
        self.health = -1
        self.initial_loc = -1
        self.ent_zero1 = -1

    def tozero(self, x, y):
        """ Zeroes out the entity object.  Apart from x and y, which are passed in. """
        self.x = x
        self.y = y
        self.entid = 1
        self.direction = 1
        self.entscript = ''
        if (self.savegame):
            self.friendly = 0
            self.unknownc1 = 0
            self.health = 0
            self.initial_loc = 0
            self.ent_zero1 = 0
            self.set_initial(x, y)

        # Call out to superclass zeroing
        self._sub_tozero()

    def _sub_tozero(self):
        """
        Function for superclasses to override with zeroing functions.
        """
        pass

    def replicate(self):
        newentity = Entity()

        # Simple Values
        newentity.savegame = self.savegame
        newentity.entid = self.entid
        newentity.x = self.x
        newentity.y = self.y
        newentity.direction = self.direction
        newentity.entscript = self.entscript
        newentity.friendly = self.friendly
        newentity.unknownc1 = self.unknownc1
        newentity.health = self.health
        newentity.initial_loc = self.initial_loc
        newentity.ent_zero1 = self.ent_zero1

        # Call out to superclass replication
        self._sub_replicate(newentity)

        # ... aaand return our new object
        return newentity

    def _sub_replicate(self, newentity):
        """
        Stub for superclasses to override, to replicate specific vars
        """
        pass

    def equals(self, entity):
        """
        Compare ourselves to another entity object.  We're just
        checking if our values are the same, NOT if we're *actually*
        the same object.  Returns true for equality, false for inequality.
        """
        return (self._sub_equals(entity) and
                self.x == entity.x and
                self.y == entity.y and
                self.entid == entity.entid and
                self.direction == entity.direction and
                self.entscript == entity.entscript and
                self.savegame == entity.savegame and
                self.friendly == entity.friendly and
                self.unknownc1 == entity.unknownc1 and
                self.health == entity.health and
                self.initial_loc == entity.initial_loc and
                self.ent_zero1 == entity.ent_zero1)

    def _sub_equals(self, entity):
        """
        Stub for superclasses to override, to replicate specific vars
        """
        pass

    def set_initial(self, x, y):
        """
        Set our initial_loc parameter, given actual (x,y) coordinates.
        """
        self.initial_loc = (y*100)+x

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        ret = []

        if (self.entid in c.entitytable):
            ret.append("\tEntity: %s" % (c.entitytable[self.entid].name))
        else:
            ret.append("\tEntity ID: %d" % (self.entid))
        ret.append("\tMap Location: (%d, %d)" % (self.x, self.y))
        if (self.direction in c.dirtable):
            ret.append("\tFacing %s" % (c.dirtable[self.direction]))
        else:
            ret.append("\tDirection ID: %d" % (self.direction))
        ret.append("\tScript: %s" % self.entscript)
        if (self.savegame):
            ret.append("\tFriendly: %d" % (self.friendly))
            ret.append("\tHealth: %d" % (self.health))
            ret.append("\tInitial Tile: %d" % self.initial_loc)
            if self.book == 2:
                ret.append("\tMovement Flag: %d" % (self.movement))
                for (i, status) in enumerate(self.statuses):
                    if status != 0:
                        if i in c.statustable:
                            statusstr = c.statustable[i]
                        else:
                            statusstr = 'Unknown Status "%d"' % (i)
                        ret.append("\t%s: %d" % (statusstr, status))
            if (unknowns):
                ret.append("\tUnknown value 1 (generally 1 or 2): %d" % self.unknownc1)
                if self.book == 1:
                    ret.append("\tUnknown value 2 (generally 0 or 1): %d" % self.unknownc2)
                ret.append("\tUsually Zero (1): %d" % self.ent_zero1)
                if self.book == 1:
                    ret.append("\tUsually Zero (2): %d" % self.ent_zero2)
        else:
            ret.append( "\t(No extra attributes - this is the base map definition file)")

        return "\n".join(ret)

    @staticmethod
    def new(book, savegame):
        """
        Static method to initialize the correct object
        """
        if book == 1:
            return B1Entity(savegame)
        else:
            return B2Entity(savegame)

class B1Entity(Entity):
    """
    Entity structure for Book 1
    """

    book = 1
    form_elements = [ 'unknownc1_label', 'unknownc1',
            'ent_zero2_label', 'ent_zero2'
            ]

    def __init__(self, savegame):
        super(B1Entity, self).__init__(savegame)

        # B1-specific elements
        self.unknownc2 = -1
        self.ent_zero2 = -1

    def _sub_tozero(self):
        """
        To-zero for B1 elements
        """
        self.unknownc2 = 0
        self.ent_zero2 = 0

    def _sub_replicate(self, newentity):
        """
        Replication for B1 elements
        """
        newentity.unknownc2 = self.unknownc2
        newentity.ent_zero2 = self.ent_zero2

    def _sub_equals(self, entity):
        """
        Equality function for B1
        """
        return (self.unknownc2 == entity.unknownc2 and
                self.ent_zero2 == entity.ent_zero2)

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
        self.entscript = df.readstr()
        if (self.savegame):
            self.friendly = df.readuchar()
            self.unknownc1 = df.readuchar()
            self.health = df.readint()
            self.unknownc2 = df.readuchar()
            self.initial_loc = df.readshort()
            self.ent_zero1 = df.readuchar()
            self.ent_zero2 = df.readuchar()

    def write(self, df):
        """ Write the entity to the file. """

        df.writeuchar(self.entid)
        df.writeuchar(self.x)
        df.writeuchar(self.y)
        df.writeuchar(self.direction)
        df.writestr(self.entscript)
        if (self.savegame):
            df.writeuchar(self.friendly)
            df.writeuchar(self.unknownc1)
            df.writeint(self.health)
            df.writeuchar(self.unknownc2)
            df.writeshort(self.initial_loc)
            df.writeuchar(self.ent_zero1)
            df.writeuchar(self.ent_zero2)

class B2Entity(Entity):
    """
    Entity structure for Book 2
    """

    book = 2
    form_elements = [ 'movement_label', 'movement' ]

    def __init__(self, savegame):
        super(B2Entity, self).__init__(savegame)

        # B2-specific vars
        self.movement = -1
        self.statuses = []

    def _sub_tozero(self):
        """
        To-zero for B1 elements
        """
        self.movement = 0
        self.statuses = []
        for i in range(26):
            self.statuses.append(0)

    def _sub_replicate(self, newentity):
        """
        Replication for B1 elements
        """
        newentity.movement = self.movement
        newentity.statuses = []
        for status in self.statuses:
            newentity.statuses.append(status)

    def _sub_equals(self, entity):
        """
        Equality function for B1
        """
        if len(self.statuses) != len(entity.statuses):
            return False
        for (mystatus, newstatus) in zip(self.statuses, entity.statuses):
            if mystatus != newstatus:
                return False
        return (self.movement == entity.movement)

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
        self.entscript = df.readstr()
        if (self.savegame):
            self.friendly = df.readuchar()
            self.movement = df.readuchar()
            self.health = df.readint()
            self.unknownc1 = df.readuchar()
            self.initial_loc = df.readshort()
            self.ent_zero1 = df.readshort()
            self.statuses = []
            for i in range(26):
                self.statuses.append(df.readint())

    def write(self, df):
        """ Write the entity to the file. """

        df.writeuchar(self.entid)
        df.writeuchar(self.x)
        df.writeuchar(self.y)
        df.writeuchar(self.direction)
        df.writestr(self.entscript)
        if (self.savegame):
            df.writeuchar(self.friendly)
            df.writeuchar(self.movement)
            df.writeint(self.health)
            df.writeuchar(self.unknownc1)
            df.writeshort(self.initial_loc)
            df.writeshort(self.ent_zero1)
            for status in self.statuses:
                df.writeint(status)
