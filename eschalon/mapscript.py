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

import struct
from eschalonb1.item import Item
from eschalonb1.savefile import FirstItemLoadException

class Mapscript:
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
        self.unknownh1 = -1
        self.zeroi2 = -1
        self.zeroi3 = -1
        self.unknownh2 = -1
        self.flags = -1
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
        self.unknownh1 = 0
        self.zeroi2 = 0
        self.zeroi3 = 0
        self.unknownh2 = 0
        self.flags = 0
        self.unknownh3 = 0
        self.script = ''

        # Populate Items as well
        for num in range(8):
            self.items.append(Item())
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
        newmapscript.unknownh1 = self.unknownh1
        newmapscript.zeroi2 = self.zeroi2
        newmapscript.zeroi3 = self.zeroi3
        newmapscript.unknownh2 = self.unknownh2
        newmapscript.flags = self.flags
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
        self.unknownh1 = df.readshort()
        self.zeroi2 = df.readint()
        self.zeroi3 = df.readint()
        self.unknownh2 = df.readshort()
        self.flags = df.readshort()
        self.unknownh3 = df.readshort()
        self.script = df.readstr()

        # Items
        for num in range(8):
            self.items.append(Item())
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
        df.writeshort(self.unknownh1)
        df.writeint(self.zeroi2)
        df.writeint(self.zeroi3)
        df.writeshort(self.unknownh2)
        df.writeshort(self.flags)
        df.writeshort(self.unknownh3)
        df.writestr(self.script)

        for num in range(8):
            if (self.savegame):
                self.items[num].write(df)
            else:
                df.writestr(self.items[num].item_name)

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        ret = []

        ret.append("\tMap Location: (%d, %d)" % (self.x, self.y))
        ret.append("\tDescription / Map Link: %s" % self.description)
        ret.append("\tExtra Text / Map Link Destination: %s" % self.extratext)
        ret.append("\tScript: %s" % self.script)
        ret.append("\tContents:")
        for item in self.items:
            if (item.item_name != ''):
                ret.append("\t\t* %s" % item.item_name)
        if (unknowns):
            ret.append("\tFlags (probably): %d 0x%04X" % (self.flags, self.flags))
            ret.append("\tUnknown Short 1: %d 0x%04X" % (self.unknownh1, self.unknownh1))
            ret.append("\tUnknown Short 2: %d 0x%04X" % (self.unknownh2, self.unknownh2))
            ret.append("\tUnknown Short 3: %d 0x%04X" % (self.unknownh3, self.unknownh3))
            ret.append("\tUsually Zero 1: %d" % (self.zeroh1))
            ret.append("\tUsually Zero 2: %d" % (self.zeroi1))
            ret.append("\tUsually Zero 3: %d" % (self.zeroi2))
            ret.append("\tUsually Zero 4: %d" % (self.zeroi3))

        return "\n".join(ret)
