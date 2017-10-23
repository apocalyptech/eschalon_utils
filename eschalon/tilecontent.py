#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2014 CJ Kucera, Elliot Kendall
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
import logging

from eschalon.constants import constants as c
from eschalon.item import Item
from eschalon.savefile import FirstItemLoadException

LOG = logging.getLogger(__name__)




class Tilecontent(object):
    """
    A class to hold data about a particular tilecontent on a map.
    This is basically just a collection of extra properties on the tile
    which make it more interesting.  In the GUI we refer to these as
    "objects," but that name wouldn't play nicely with code.  These
    objects are typically used to describe torch sconces, containers (barrels,
    chests, and the like), traps, and level exits (stairs, ladders, dungeon
    exits, etc).
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
        newtilecontent = Tilecontent.new(self.book, self.savegame)

        # Simple Values
        newtilecontent.savegame = self.savegame
        newtilecontent.x = self.x
        newtilecontent.y = self.y
        newtilecontent.description = self.description
        newtilecontent.extratext = self.extratext
        newtilecontent.lock = self.lock
        newtilecontent.trap = self.trap
        newtilecontent.state = self.state
        newtilecontent.script = self.script

        # Items
        for item in self.items:
            newtilecontent.items.append(item.replicate())

        # Call out to superclass replication
        self._sub_replicate(newtilecontent)

        # ... aaand return our new object
        return newtilecontent

    def _sub_replicate(self, newtilecontent):
        """
        Stub for superclasses to override, to replicate specific vars
        """
        pass

    def _convert_savegame(self, savegame):
        """
        Converts ourself to a savegame or global object.  This could be
        overridden by implementing classes if needed.
        """
        for item in self.items:
            item._convert_savegame(savegame)
        self.savegame = savegame

    def equals(self, tilecontent):
        """
        Compare ourselves to another tilecontent object.  We're just
        checking if our values are the same, NOT if we're *actually*
        the same object.  Returns true for equality, false for inequality.
        """
        return (self._sub_equal(tilecontent) and
                self.x == tilecontent.x and
                self.y == tilecontent.y and
                self.description == tilecontent.description and
                self.extratext == tilecontent.extratext and
                self.lock == tilecontent.lock and
                self.trap == tilecontent.trap and
                self.state == tilecontent.state and
                self.script == tilecontent.script and
                self.savegame == tilecontent.savegame and
                self.items_equal(tilecontent.items))

    def _sub_equal(self, tilecontent):
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
            return B1Tilecontent(savegame)
        elif book == 2:
            return B2Tilecontent(savegame)
        elif book == 3:
            return B3Tilecontent(savegame)


class B1Tilecontent(Tilecontent):
    """
    Object structure for Book 1
    """

    book = 1

    def __init__(self, savegame):
        super(B1Tilecontent, self).__init__(savegame)

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

    def _sub_replicate(self, newtilecontent):
        """
        Replication!
        """
        newtilecontent.zeroi1 = self.zeroi1
        newtilecontent.zeroh1 = self.zeroh1
        newtilecontent.sturdiness = self.sturdiness
        newtilecontent.flags = self.flags
        newtilecontent.zeroi2 = self.zeroi2
        newtilecontent.zeroi3 = self.zeroi3
        newtilecontent.other = self.other
        newtilecontent.unknownh3 = self.unknownh3

    def _sub_equal(self, tilecontent):
        """
        Whether our B1-specific vars are equal
        """
        return (self.zeroi1 == tilecontent.zeroi1 and
                self.zeroh1 == tilecontent.zeroh1 and
                self.sturdiness == tilecontent.sturdiness and
                self.flags == tilecontent.flags and
                self.zeroi2 == tilecontent.zeroi2 and
                self.zeroi3 == tilecontent.zeroi3 and
                self.other == tilecontent.other and
                self.unknownh3 == tilecontent.unknownh3)

    def read(self, df):
        """ Given a file descriptor, read in the tilecontent. """

        # We throw an exception because there seems to be an arbitrary
        # number of tilecontents at the end of the map file, and no
        # 'tilecontent count' anywhere.  So we have to just keep loading
        # tilecontents until EOF,
        if (df.eof()):
            raise FirstItemLoadException('Reached EOF')

        # I'd just like to say "wtf" at this coordinate-storing system
        intcoords = df.readint()
        self.x = (intcoords % 100)
        self.y = int(intcoords / 100)

        # ... everything else
        self.description = df.readstr().decode('UTF-8')
        self.extratext = df.readstr().decode('UTF-8')
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
        self.script = df.readstr().decode('UTF-8')

        # Items
        for num in range(8):
            self.items.append(Item.new(c.book))
            if (self.savegame):
                self.items[num].read(df)
            else:
                self.items[num].item_name = df.readstr().decode('UTF-8')

    def write(self, df):
        """ Write the tilecontent to the file. """

        df.writeint((self.y * 100) + self.x)
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
            for (flag, flagtext) in list(c.tilecontentflags.items()):
                if (self.flags & flag == flag):
                    ret.append("\t\t* %s" % flagtext)

        ret.append("\tContents:")
        for item in self.items:
            if (item.item_name != ''):
                ret.append("\t\t* %s" % item.item_name)
        if (unknowns):
            ret.append("\tUnknown Short 3: %d 0x%04X" %
                       (self.unknownh3, self.unknownh3))
            ret.append("\tUsually Zero 1: %d" % (self.zeroh1))
            ret.append("\tUsually Zero 2: %d" % (self.zeroi1))
            ret.append("\tUsually Zero 3: %d" % (self.zeroi2))
            ret.append("\tUsually Zero 4: %d" % (self.zeroi3))

        return "\n".join(ret)


class B2Tilecontent(Tilecontent):
    """
    Object structure for Book 2
    """

    book = 2

    def __init__(self, savegame):
        super(B2Tilecontent, self).__init__(savegame)

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

    def _sub_replicate(self, newtilecontent):
        """
        Replication!
        """
        newtilecontent.cur_condition = self.cur_condition
        newtilecontent.max_condition = self.max_condition
        newtilecontent.on_empty = self.on_empty
        newtilecontent.slider_loot = self.slider_loot

    def _sub_equal(self, tilecontent):
        """
        Whether our B2-specific vars are equal
        """
        return (self.cur_condition == tilecontent.cur_condition and
                self.max_condition == tilecontent.max_condition and
                self.on_empty == tilecontent.on_empty and
                self.slider_loot == tilecontent.slider_loot)

    def read(self, df):
        """ Given a file descriptor, read in the tilecontent. """

        # We throw an exception because there seems to be an arbitrary
        # number of tilecontents at the end of the map file, and no
        # 'tilecontent count' anywhere.  So we have to just keep loading
        # tilecontents until EOF,
        if (df.eof()):
            raise FirstItemLoadException('Reached EOF')

        # I'd just like to say "wtf" at this coordinate-storing system
        intcoords = df.readint()
        self.x = (intcoords % 100)
        self.y = int(intcoords / 100)

        # ... everything else
        self.description = df.readstr().decode('UTF-8')
        self.extratext = df.readstr().decode('UTF-8')
        self.cur_condition = df.readint()
        self.max_condition = df.readint()
        self.on_empty = df.readuchar()
        self.lock = df.readuchar()
        self.trap = df.readuchar()
        self.slider_loot = df.readshort()
        self.state = df.readuchar()
        self.script = df.readstr().decode('UTF-8')

        # Items
        for num in range(8):
            self.items.append(Item.new(self.book))
            if (self.savegame):
                self.items[num].read(df)
            else:
                self.items[num].item_name = df.readstr().decode('UTF-8')

    def write(self, df):
        """ Write the tilecontent to the file. """

        df.writeint((self.y * 100) + self.x)
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

        ret.append("\tCondition: %d / %d" %
                   (self.cur_condition, self.max_condition))
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


class B3Tilecontent(B2Tilecontent):
    """
    Object structure for Book 3
    """

    # The file format is identical, so we don't need to override anything
    book = 3
