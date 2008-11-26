#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
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
from eschalonb1.savefile import Savefile
from eschalonb1.square import Square
from eschalonb1.exit import Exit
from eschalonb1.loadexception import LoadException

class Map:
    """ The base Map class.  """

    def __init__(self, filename):
        """ A fresh object. """

        self.df = None
        self.mapid = ''
        self.mapname = ''
        self.soundfile1 = ''
        self.unknowns1 = ''
        self.unknowns2 = ''
        self.unknowns3 = ''
        self.unknowns4 = ''
        self.unknowns5 = ''
        self.skybox = ''
        self.soundfile2 = ''
        self.unknowni1 = -1
        self.unknownh1 = -1

        # This is pure supposition at this point, but it seems to fit
        self.color_r = -1
        self.color_g = -1
        self.color_b = -1
        self.color_a = -1

        self.unknowni2 = -1
        self.unknowni3 = -1
        self.unknowni4 = -1
        self.unknowni5 = -1
        self.unknowni6 = -1
        self.unknowni7 = -1

        self.extradata = ''

        self.cursqcol = 0
        self.cursqrow = 0

        self.squares = []
        for i in range(200):
            self.squares.append([])
            for j in range(100):
                self.squares[i].append(Square())

        self.exits = []

        self.df = Savefile(filename)

    def replicate(self):
        # Note that this could, theoretically, lead to contention issues, since
        # Savefile doesn't as yet lock the file.  So, er, be careful for now, I
        # guess.
        newmap = Map(self.df.filename)

        # Single vals (no need to do actual replication)
        newmap.mapid = self.mapid
        newmap.mapname = self.mapname
        newmap.soundfile1 = self.soundfile1
        newmap.unknowns1 = self.unknowns1
        newmap.unknowns2 = self.unknowns2
        newmap.unknowns3 = self.unknowns3
        newmap.unknowns4 = self.unknowns4
        newmap.unknowns5 = self.unknowns5
        newmap.skybox = self.skybox
        newmap.soundfile2 = self.soundfile2
        newmap.unknowni1 = self.unknowni1
        newmap.unknownh1 = self.unknownh1
        newmap.color_r = self.color_r
        newmap.color_g = self.color_g
        newmap.color_b = self.color_b
        newmap.color_a = self.color_a
        newmap.unknowni2 = self.unknowni2
        newmap.unknowni3 = self.unknowni3
        newmap.unknowni4 = self.unknowni4
        newmap.unknowni5 = self.unknowni5
        newmap.unknowni6 = self.unknowni6
        newmap.unknowni7 = self.unknowni7
        newmap.extradata = self.extradata

        # Objects that need copying
        for i in range(200):
            for j in range(100):
                newmap.squares[i][j] = self.squares[i][j].replicate()
        for exit in self.exits:
            if (exit is None):
                newmap.exits.append(None)
            else:
                newmap.exits.append(exit.replicate())

        # Now return our duplicated object
        return newmap

    def addsquare(self):
        """ Add a new square, assuming that the squares are stored in a
            left-to-right, top-to-bottom format in the map. """
        self.squares[self.cursqrow][self.cursqcol].read(self.df)
        self.cursqcol = self.cursqcol + 1
        if (self.cursqcol == 100):
            self.cursqcol = 0
            self.cursqrow = self.cursqrow + 1

    def addexit(self):
        """ Add an exit. """
        self.exits.append(Exit().read(self.df))

    def read(self):
        """ Read in the whole map from a file descriptor. """

        try:

            # Open the file
            self.df.open_r()

            # Start processing
            self.mapid = self.df.readstr()
            self.mapname = self.df.readstr()
            self.soundfile1 = self.df.readstr()
            self.unknowns1 = self.df.readstr()
            self.unknowns2 = self.df.readstr()
            self.unknowns3 = self.df.readstr()
            self.unknowns4 = self.df.readstr()
            self.unknowns5 = self.df.readstr()
            self.skybox = self.df.readstr()
            self.soundfile2 = self.df.readstr()
            self.unknowni1 = self.df.readint()
            self.unknownh1 = self.df.readshort()

            self.color_r = self.df.readuchar()
            self.color_g = self.df.readuchar()
            self.color_b = self.df.readuchar()
            self.color_a = self.df.readuchar()

            self.unknowni2 = self.df.readint()
            self.unknowni3 = self.df.readint()
            self.unknowni4 = self.df.readint()
            self.unknowni5 = self.df.readint()
            self.unknowni6 = self.df.readint()
            self.unknowni7 = self.df.readint()

            # Squares
            for i in range(200*100):
                self.addsquare()

            # Exits
            for i in range(2):
                self.addexit()

            # If there's extra data at the end, we likely don't have
            # a valid char file
            self.extradata = self.df.read()
            #if (len(self.extradata)>0):
            #    raise LoadException('Extra data at end of file')

            # Close the file
            self.df.close()

        except (IOError, struct.error), e:
            raise LoadException(str(e))

    def write(self):
        """ Writes out the map to the file descriptor. """
        
        # Open the file
        self.df.open_w()

        # Start
        self.df.writestr(self.mapid)
        self.df.writestr(self.mapname)
        self.df.writestr(self.soundfile1)
        self.df.writestr(self.unknowns1)
        self.df.writestr(self.unknowns2)
        self.df.writestr(self.unknowns3)
        self.df.writestr(self.unknowns4)
        self.df.writestr(self.unknowns5)
        self.df.writestr(self.skybox)
        self.df.writestr(self.soundfile2)
        self.df.writeint(self.unknowni1)
        self.df.writeshort(self.unknownh1)
        self.df.writeuchar(self.color_r)
        self.df.writeuchar(self.color_g)
        self.df.writeuchar(self.color_b)
        self.df.writeuchar(self.color_a)
        self.df.writeint(self.unknowni2)
        self.df.writeint(self.unknowni3)
        self.df.writeint(self.unknowni4)
        self.df.writeint(self.unknowni5)
        self.df.writeint(self.unknowni6)
        self.df.writeint(self.unknowni7)

        # Squares
        for row in self.squares:
            for square in row:
                square.write(self.df)

        # Exits
        for exit in self.exits:
            exit.write(self.df)

        # Any extra data we might have
        if (len(self.extradata) > 0):
            self.df.writestr(self.extradata)

        # Clean up
        self.df.close()

