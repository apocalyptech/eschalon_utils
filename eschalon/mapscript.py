#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Savefile Editor
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
from eschalon.item import Item
from eschalon.savefile import FirstItemLoadException

class Mapscript(object):
    """
    A class to hold data about a particular mapscript on a map.
    Calling this a "script" is something of a misnomer, actually.  These
    objects are typically used to describe torch sconces, containers (barrels,
    chests, and the like), traps, and level exits (stairs, ladders, dungeon
    exits, etc).  I'm just keeping the name rather than rename it, though.
    """

    def __init__(self, savegame=True):
        """ A fresh object with no data. """

        self.savegame = savegame
        self.x = -1
        self.y = -1
        self.description = ''
        self.extratext = ''
        self.zeroi1 = -1
        self.zeroh1 = -1
        self.sturdiness = -1
        self.flags = -1
        self.zeroi2 = -1
        self.zeroi3 = -1
        self.lock = -1
        self.trap = -1
        self.state = -1
        self.other = -1
        self.unknownh3 = -1
        self.script = ''

        self.items = []

    def tozero(self, x, y):
        """ Zeroes out the object. """
        self.x = x
        self.y = y
        self.description = ''
        self.extratext = ''
        self.zeroi1 = 0
        self.zeroh1 = 0
        self.sturdiness = 0
        self.flags = 0
        self.zeroi2 = 0
        self.zeroi3 = 0
        self.lock = 0
        self.trap = 0
        self.state = 0
        self.other = 0
        self.unknownh3 = 0
        self.script = ''

        # Populate Items as well
        for num in range(8):
            self.items.append(Item.new(c.book))
            self.items[num].tozero()

    def replicate(self):
        newmapscript = Mapscript()

        # Simple Values
        newmapscript.savegame = self.savegame
        newmapscript.x = self.x
        newmapscript.y = self.y
        newmapscript.description = self.description
        newmapscript.extratext = self.extratext
        newmapscript.zeroi1 = self.zeroi1
        newmapscript.zeroh1 = self.zeroh1
        newmapscript.sturdiness = self.sturdiness
        newmapscript.flags = self.flags
        newmapscript.zeroi2 = self.zeroi2
        newmapscript.zeroi3 = self.zeroi3
        newmapscript.lock = self.lock
        newmapscript.trap = self.trap
        newmapscript.state = self.state
        newmapscript.other = self.other
        newmapscript.unknownh3 = self.unknownh3
        newmapscript.script = self.script

        # Items
        for item in self.items:
            newmapscript.items.append(item.replicate())

        # ... aaand return our new object
        return newmapscript

    def read(self, df):
        """ Given a file descriptor, read in the mapscript. """

        # We throw an exception because there seems to be an arbitrary
        # number of scripts at the end of the map file, and no 'script count' anywhere.
        # So we have to just keep loading scripts until EOF,
        if (df.eof()):
            raise FirstItemLoadException('Reached EOF')

        # I'd just like to say "wtf" at this coordinate-storing system
        intcoords = df.readint()
        self.x = (intcoords % 100)
        self.y = int(intcoords / 100)

        # ... everything else
        self.description = df.readstr()
        self.extratext = df.readstr()
        self.zeroi1 = df.readint()
        self.zeroh1 = df.readshort()
        self.sturdiness = df.readuchar()
        self.flags = df.readuchar()
        self.zeroi2 = df.readint()
        self.zeroi3 = df.readint()
        self.lock = df.readuchar()
        self.trap = df.readuchar()
        self.other = df.readuchar()
        self.state = df.readuchar()
        self.unknownh3 = df.readshort()
        self.script = df.readstr()

        # Items
        for num in range(8):
            self.items.append(Item.new(c.book))
            if (self.savegame):
                self.items[num].read(df)
            else:
                self.items[num].item_name = df.readstr()

    def write(self, df):
        """ Write the mapscript to the file. """

        df.writeint((self.y*100)+self.x)
        df.writestr(self.description)
        df.writestr(self.extratext)
        df.writeint(self.zeroi1)
        df.writeshort(self.zeroh1)
        df.writeuchar(self.sturdiness)
        df.writeuchar(self.flags)
        df.writeint(self.zeroi2)
        df.writeint(self.zeroi3)
        df.writeuchar(self.lock)
        df.writeuchar(self.trap)
        df.writeuchar(self.other)
        df.writeuchar(self.state)
        df.writeshort(self.unknownh3)
        df.writestr(self.script)

        for num in range(8):
            if (self.savegame):
                self.items[num].write(df)
            else:
                df.writestr(self.items[num].item_name)

    def equals(self, script):
        """
        Compare ourselves to another script object.  We're just
        checking if our values are the same, NOT if we're *actually*
        the same object.  Returns true for equality, false for inequality.
        """
        return (self.x == script.x and
                self.y == script.y and
                self.description == script.description and
                self.extratext == script.extratext and
                self.zeroi1 == script.zeroi1 and
                self.zeroh1 == script.zeroh1 and
                self.sturdiness == script.sturdiness and
                self.flags == script.flags and
                self.zeroi2 == script.zeroi2 and
                self.zeroi3 == script.zeroi3 and
                self.lock == script.lock and
                self.trap == script.trap and
                self.state == script.state and
                self.other == script.other and
                self.unknownh3 == script.unknownh3 and
                self.script == script.script and
                self.savegame == script.savegame and
                self.items_equal(script.items))

    def items_equal(self, items):
        """
        Compare the contents of our items to the contents of the
        given items.
        """
        if (len(self.items) != len(items)):
            return False
        for (myitem, compitem) in zip(self.items, items):
            if (not myitem.equals(compitem)):
                return False
        return True

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        ret = []

        ret.append("\tMap Location: (%d, %d)" % (self.x, self.y))
        ret.append("\tDescription / Map Link: %s" % self.description)
        ret.append("\tExtra Text / Map Link Destination: %s" % self.extratext)
        ret.append("\tScript: %s" % self.script)
        ret.append("\tLock Level: %d" % self.lock)
        if (self.lock == 99):
            ret.append("\tSlider Lock Code: %d" % self.other)
        else:
            ret.append("\tOther (typically 0-3): %d" % self.other)
        if (self.trap in c.traptable):
            ret.append("\tTrapped: %s" % c.traptable[self.trap])
        else:
            ret.append("\tTrapped: %d (unknown)" % self.trap)
        if (self.state in c.containertable):
            ret.append("\tState: %s" % c.containertable[self.state])
        else:
            ret.append("\tState: %d (unknown)" % self.state)
        ret.append("\tSturdiness: %d" % self.sturdiness)
        if (self.flags != 0):
            ret.append("\tFlags:")
            for (flag, flagtext) in c.scriptflags.items():
                if (self.flags & flag == flag):
                    ret.append("\t\t* %s" % flagtext)

        ret.append("\tContents:")
        for item in self.items:
            if (item.item_name != ''):
                ret.append("\t\t* %s" % item.item_name)
        if (unknowns):
            ret.append("\tUnknown Short 3: %d 0x%04X" % (self.unknownh3, self.unknownh3))
            ret.append("\tUsually Zero 1: %d" % (self.zeroh1))
            ret.append("\tUsually Zero 2: %d" % (self.zeroi1))
            ret.append("\tUsually Zero 3: %d" % (self.zeroi2))
            ret.append("\tUsually Zero 4: %d" % (self.zeroi3))

        return "\n".join(ret)
