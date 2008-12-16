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
from eschalonb1.savefile import FirstItemLoadException

class Mapscript:
    """ A class to hold data about a particular mapscript on a map. """

    def __init__(self, savegame=True):
        """ A fresh object with no data. """

        self.savegame = savegame
        self.x = -1
        self.y = -1
        self.mapid = ''
        self.number = ''    # apparently the coords of where to spawn on the new map, Y before X (and no delimiter?), or user text
        self.unknowni2 = -1
        self.unknowni3 = -1
        self.unknowni4 = -1
        self.unknowni5 = -1
        self.unknowni6 = -1
        self.unknownh1 = -1
        self.script = ''

        self.block_unknown_i_1 = []
        self.block_unknown_s_1 = []
        self.block_unknown_i_2 = []
        self.block_unknown_s_2 = []
        self.block_unknown_i_3 = []

    def replicate(self):
        newmapscript = Mapscript()

        # Simple Values
        newmapscript.savegame = self.savegame
        newmapscript.x = self.x
        newmapscript.y = self.y
        newmapscript.mapid = self.mapid
        newmapscript.number = self.number
        newmapscript.unknowni2 = self.unknowni2
        newmapscript.unknowni3 = self.unknowni3
        newmapscript.unknowni4 = self.unknowni4
        newmapscript.unknowni5 = self.unknowni5
        newmapscript.unknowni6 = self.unknowni6
        newmapscript.unknownh1 = self.unknownh1
        newmapscript.script = self.script

        # Arrays
        for val in self.block_unknown_s_1:
            newmapscript.block_unknown_s_1.append(val)
        for val in self.block_unknown_i_1:
            newmapscript.block_unknown_i_1.append(val)

        # Arrays-of-arrays
        for val in self.block_unknown_i_2:
            newmapscript.block_unknown_i_2.append([])
            cur_idx = len(newmapscript.block_unknown_i_2)-1
            for val2 in val:
                newmapscript.block_unknown_i_2[cur_idx].append(val2)

        for val in self.block_unknown_s_2:
            newmapscript.block_unknown_s_2.append([])
            cur_idx = len(newmapscript.block_unknown_s_2)-1
            for val2 in val:
                newmapscript.block_unknown_s_2[cur_idx].append(val2)

        for val in self.block_unknown_i_3:
            newmapscript.block_unknown_i_3.append([])
            cur_idx = len(newmapscript.block_unknown_i_3)-1
            for val2 in val:
                newmapscript.block_unknown_i_3[cur_idx].append(val2)

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
        self.mapid = df.readstr()
        self.number = df.readstr()
        self.unknowni2 = df.readint()
        self.unknowni3 = df.readint()
        self.unknowni4 = df.readint()
        self.unknowni5 = df.readint()
        self.unknowni6 = df.readint()
        self.unknownh1 = df.readshort()
        self.script = df.readstr()

        # Blocks of information, most of which doesn't exist for global maps
        for num in range(8):
            if (self.savegame):
                self.block_unknown_i_1.append(df.readint())
            self.block_unknown_s_1.append(df.readstr())
            if (self.savegame):
                cur_idx = len(self.block_unknown_s_1)-1
                self.block_unknown_i_2.append([])
                self.block_unknown_s_2.append([])
                self.block_unknown_i_3.append([])
                for num2 in range(21):
                    self.block_unknown_i_2[cur_idx].append(df.readint())
                for num2 in range(2):
                    self.block_unknown_s_2[cur_idx].append(df.readstr())
                for num2 in range(2):
                    self.block_unknown_i_3[cur_idx].append(df.readint())

    def write(self, df):
        """ Write the mapscript to the file. """

        df.writeint((self.y*100)+self.x)
        df.writestr(self.mapid)
        df.writestr(self.number)
        df.writeint(self.unknowni2)
        df.writeint(self.unknowni3)
        df.writeint(self.unknowni4)
        df.writeint(self.unknowni5)
        df.writeint(self.unknowni6)
        df.writeshort(self.unknownh1)
        df.writestr(self.script)

        for num in range(8):
            if (self.savegame):
                df.writeint(self.block_unknown_i_1[num])
            df.writestr(self.block_unknown_s_1[num])
            # We'll do some extra processing here, mostly in case the 'savegame'
            # flag gets flipped, so the written file would be valid
            if (self.savegame):
                for num2 in range(21):
                    if (num in self.block_unknown_i_2 and num2 in self.block_unknown_i_2[num]):
                        self.writeint(self.block_unknown_i_2[num][num2])
                    else:
                        self.writeint(0)
                for num2 in range(2):
                    if (num in self.block_unknown_s_2 and num2 in self.block_unknown_s_2[num]):
                        self.writestr(self.block_unknown_s_2[num][num2])
                    else:
                        self.writestr('')
                for num2 in range(2):
                    if (num in self.block_unknown_i_3 and num2 in self.block_unknown_i_3[num]):
                        self.writeint(self.block_unknown_i_3[num][num2])
                    else:
                        self.writeint(0)

    def display(self, unknowns=False):
        """ Show a textual description of all fields. """

        ret = []

        ret.append("\tMap ID: %s" % self.mapid)
        ret.append("\tMap Location: (%d, %d)" % (self.x, self.y))
        ret.append("\tScript: %s" % self.script)
        if (unknowns):
            ret.append("\tA Number: %s" % self.number)
            ret.append("\tUnknown Integer 2: %d" % self.unknowni2)
            ret.append("\tUnknown Integer 3: %d" % self.unknowni3)
            ret.append("\tUnknown Integer 4: %d" % self.unknowni4)
            ret.append("\tUnknown Integer 5: %d" % self.unknowni5)
            ret.append("\tUnknown Integer 6: %d" % self.unknowni6)
            ret.append("\tUnknown Short 1: %d" % self.unknownh1)
            ret.append("\tUnknown String 1: %s" % self.unknowns1)
            ret.append("\tUnknown String 2: %s" % self.unknowns2)
            ret.append("\tUnknown String 3: %s" % self.unknowns3)
            ret.append("\tUnknown String 4: %s" % self.unknowns4)
            ret.append("\tUnknown String 5: %s" % self.unknowns5)
            ret.append("\tUnknown String 6: %s" % self.unknowns6)
            ret.append("\tUnknown String 7: %s" % self.unknowns7)
            ret.append("\tUnknown String 8: %s" % self.unknowns8)

        return "\n".join(ret)
