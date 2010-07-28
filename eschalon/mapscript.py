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

        # Common attributes
        self.savegame = savegame
        self.x = -1
        self.y = -1
        self.description = ''
        self.extratext = ''
        self.lock = -1
        self.trap = -1
        self.state = -1
        self.script = ''

        self.items = []

    def tozero(self, x, y):
        """ Zeroes out the object. """
        self.x = x
        self.y = y
        self.description = ''
        self.extratext = ''
        self.lock = 0
        self.trap = 0
        self.state = 0
        self.script = ''

        # Populate Items as well
        for num in range(8):
            self.items.append(Item.new(c.book))
            self.items[num].tozero()

        # Call out to superclass zeroing
        self._sub_tozero()

    def _sub_tozero(self):
        """
        Function for superclasses to override with zeroing functions.
        """
        pass

    def replicate(self):
        newmapscript = Mapscript()

        # Simple Values
        newmapscript.savegame = self.savegame
        newmapscript.x = self.x
        newmapscript.y = self.y
        newmapscript.description = self.description
        newmapscript.extratext = self.extratext
        newmapscript.lock = self.lock
        newmapscript.trap = self.trap
        newmapscript.state = self.state
        newmapscript.script = self.script

        # Items
        for item in self.items:
            newmapscript.items.append(item.replicate())

        # Call out to superclass replication
        self._sub_replicate(newmapscript)

        # ... aaand return our new object
        return newmapscript

    def _sub_replicate(self, newmapscript):
        """
        Stub for superclasses to override, to replicate specific vars
        """
        pass

    def equals(self, script):
        """
        Compare ourselves to another script object.  We're just
        checking if our values are the same, NOT if we're *actually*
        the same object.  Returns true for equality, false for inequality.
        """
        return (self._sub_equal(script) and
                self.x == script.x and
                self.y == script.y and
                self.description == script.description and
                self.extratext == script.extratext and
                self.lock == script.lock and
                self.trap == script.trap and
                self.state == script.state and
                self.script == script.script and
                self.savegame == script.savegame and
                self.items_equal(script.items))

    def _sub_equal(self, script):
        """
        Stub for superclasses to implement
        """
        return True

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

    @staticmethod
    def new(book, savegame):
        """
        Static method to initialize the correct object
        """
        if book == 1:
            return B1Mapscript(savegame)
        else:
            return B2Mapscript(savegame)

class B1Mapscript(Mapscript):
    """
    Object structure for Book 1
    """

    book = 1

    def __init__(self, savegame):
        super(B1Mapscript, self).__init__(savegame)

        # B1-specific vars
        self.zeroi1 = -1
        self.zeroh1 = -1
        self.sturdiness = -1
        self.flags = -1
        self.zeroi2 = -1
        self.zeroi3 = -1
        self.other = -1
        self.unknownh3 = -1

    def _sub_tozero(self):
        """
        Zero out our vars
        """
        self.zeroi1 = 0
        self.zeroh1 = 0
        self.sturdiness = 0
        self.flags = 0
        self.zeroi2 = 0
        self.zeroi3 = 0
        self.other = 0
        self.unknownh3 = 0

    def _sub_replicate(self, newmapscript):
        """
        Replication!
        """
        newmapscript.zeroi1 = self.zeroi1
        newmapscript.zeroh1 = self.zeroh1
        newmapscript.sturdiness = self.sturdiness
        newmapscript.flags = self.flags
        newmapscript.zeroi2 = self.zeroi2
        newmapscript.zeroi3 = self.zeroi3
        newmapscript.other = self.other
        newmapscript.unknownh3 = self.unknownh3

    def _sub_equal(self, script):
        """
        Whether our B1-specific vars are equal
        """
        return (self.zeroi1 == script.zeroi1 and
                self.zeroh1 == script.zeroh1 and
                self.sturdiness == script.sturdiness and
                self.flags == script.flags and
                self.zeroi2 == script.zeroi2 and
                self.zeroi3 == script.zeroi3 and
                self.other == script.other and
                self.unknownh3 == script.unknownh3)

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

class B2Mapscript(Mapscript):
    """
    Object structure for Book 2
    """

    book = 2

    def __init__(self, savegame):
        super(B2Mapscript, self).__init__(savegame)

        self.cur_condition = -1
        self.max_condition = -1
        self.on_empty = -1
        self.slider_loot = -1

    def _sub_tozero(self):
        """
        Zero out our vars
        """
        self.cur_condition = 0
        self.max_condition = 0
        self.on_empty = 0
        self.slider_loot = 0

    def _sub_replicate(self, newmapscript):
        """
        Replication!
        """
        newmapscript.cur_condition = self.cur_condition
        newmapscript.max_condition = self.max_condition
        newmapscript.on_empty = self.on_empty
        newmapscript.slider_loot = self.slider_loot

    def _sub_equal(self, script):
        """
        Whether our B2-specific vars are equal
        """
        return (self.cur_condition == script.cur_condition and
                self.max_condition == script.max_condition and
                self.on_empty == script.on_empty and
                self.slider_loot == script.slider_loot)

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
        self.cur_condition = df.readint()
        self.max_condition = df.readint()
        self.on_empty = df.readuchar()
        self.lock = df.readuchar()
        self.trap = df.readuchar()
        self.slider_loot = df.readshort()
        self.state = df.readuchar()
        self.script = df.readstr()

        # Items
        for num in range(8):
            self.items.append(Item.new(self.book))
            if (self.savegame):
                self.items[num].read(df)
            else:
                self.items[num].item_name = df.readstr()

    def write(self, df):
        """ Write the mapscript to the file. """

        df.writeint((self.y*100)+self.x)
        df.writestr(self.description)
        df.writestr(self.extratext)
        df.writeint(self.cur_condition)
        df.writeint(self.max_condition)
        df.writeuchar(self.on_empty)
        df.writeuchar(self.lock)
        df.writeuchar(self.trap)
        df.writeshort(self.slider_loot)
        df.writeuchar(self.state)
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

        ret.append("\tCondition: %d / %d" % (self.cur_condition, self.max_condition))
        ret.append("\tOn-Empty flag: %d" % (self.on_empty))
        ret.append("\tLock Level: %d" % self.lock)
        if (self.lock == 12):
            ret.append("\tSlider Lock Code: %d" % self.slider_loot)
        else:
            ret.append("\tLoot Level: %d" % self.slider_loot)
        if (self.trap in c.traptable):
            ret.append("\tTrapped: %s" % c.traptable[self.trap])
        else:
            ret.append("\tTrapped: %d (unknown)" % self.trap)
        if (self.state in c.containertable):
            ret.append("\tState: %s" % c.containertable[self.state])
        else:
            ret.append("\tState: %d (unknown)" % self.state)

        ret.append("\tContents:")
        for item in self.items:
            if (item.item_name != ''):
                ret.append("\t\t* %s" % item.item_name)

        return "\n".join(ret)
