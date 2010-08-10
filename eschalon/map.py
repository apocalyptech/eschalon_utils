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

import os
import struct
from eschalon import constants as c
from eschalon.savefile import Savefile, LoadException, FirstItemLoadException
from eschalon.square import Square
from eschalon.mapscript import Mapscript
from eschalon.entity import Entity

class Map(object):
    """ The base Map class.  """

    DIR_N = 0x01
    DIR_NE = 0x02
    DIR_E = 0x04
    DIR_SE = 0x08
    DIR_S = 0x10
    DIR_SW = 0x20
    DIR_W = 0x40
    DIR_NW = 0x80

    def __init__(self, df):
        """
        A fresh object.
        """

        # Everything else follows...
        self.df = None
        self.df_ent = None
        self.filename_ent = ''
        self.mapid = ''
        self.mapname = ''
        self.soundfile1 = ''
        self.soundfile2 = ''
        self.skybox = ''
        self.soundfile3 = ''
        self.map_unknowni1 = -1

        # Not entirely sure about the alpha channel, which
        # is always zero, but it seems to make sense
        self.color_r = -1
        self.color_g = -1
        self.color_b = -1
        self.color_a = -1

        self.extradata = ''

        # Note that book 1 doesn't actually have this, but for sanity's
        # sake we're putting it in the base class
        self.tree_set = -1

        self.cursqcol = 0
        self.cursqrow = 0

        self.squares = []
        for i in range(200):
            self.squares.append([])
            for j in range(100):
                self.squares[i].append(Square.new(c.book, j, i))

        self.scripts = []
        self.entities = []

        self.df = df
        self.set_df_ent()

    def set_df_ent(self):
        self.df_ent = Savefile(self.df.filename[:self.df.filename.rindex('.map')] + '.ent')

    def replicate(self):
        
        if self.book == 1:
            newmap = B1Map(Savefile(self.df.filename))
        else:
            newmap = B2Map(Savefile(self.df.filename))

        # Single vals (no need to do actual replication)
        newmap.mapname = self.mapname
        newmap.soundfile1 = self.soundfile1
        newmap.soundfile2 = self.soundfile2
        newmap.skybox = self.skybox
        newmap.soundfile3 = self.soundfile3
        newmap.map_unknowni1 = self.map_unknowni1
        newmap.color_r = self.color_r
        newmap.color_g = self.color_g
        newmap.color_b = self.color_b
        newmap.color_a = self.color_a
        newmap.extradata = self.extradata
        newmap.tree_set = self.tree_set

        # Copy squares
        for i in range(200):
            for j in range(100):
                newmap.squares[i][j] = self.squares[i][j].replicate()

        # At this point, scripts and entities have been replicated as well;
        # loop through our list to repopulate from the new objects, so that
        # our referential comparisons still work on the new copy.
        for entity in self.entities:
            if (entity is None):
                newmap.entities.append(None)
            else:
                if (entity.y < len(newmap.squares) and entity.x < len(newmap.squares[entity.y])):
                    newmap.entities.append(newmap.squares[entity.y][entity.x].entity)
                else:
                    newmap.entities.append(entity.replicate())
        scriptidxtemp = {}
        for script in self.scripts:
            if (script is None):
                newmap.scripts.append(None)
            else:
                if (script.y < len(newmap.squares) and script.x < len(newmap.squares[script.y])):
                    key = '%d%02d' % (script.y, script.x)
                    if (key in scriptidxtemp):
                        scriptidxtemp[key] += 1
                    else:
                        scriptidxtemp[key] = 0
                    newmap.scripts.append(newmap.squares[script.y][script.x].scripts[scriptidxtemp[key]])
                else:
                    newmap.scripts.append(script.replicate())

        # Call out to superclass replication
        self._sub_replicate(newmap)

        # Now return our duplicated object
        return newmap

    def _sub_replicate(self, newmap):
        """
        Stub for superclasses to override, to replicate specific vars
        """
        pass

    def set_square_savegame(self):
        """ Sets the savegame flag appropriately for all squares """
        savegame = self.is_savegame()
        for row in self.squares:
            for square in row:
                square.savegame = savegame

    def addsquare(self):
        """ Add a new square, assuming that the squares are stored in a
            left-to-right, top-to-bottom format in the map. """
        self.squares[self.cursqrow][self.cursqcol].read(self.df)
        self.cursqcol = self.cursqcol + 1
        if (self.cursqcol == 100):
            self.cursqcol = 0
            self.cursqrow = self.cursqrow + 1

    def addscript(self):
        """ Add a mapscript. """
        try:
            script = Mapscript.new(c.book, self.is_savegame())
            script.read(self.df)
            # Note that once we start deleting scripts, you'll have to update both constructs here.
            # Something along the lines of this should do:
            #   self.map.squares[y][x].scripts.remove(script)
            #   self.scripts.remove(script)
            # ... does that object then get put into a garbage collector or something?  Do we have to
            # set that to None at some point, manually?
            self.scripts.append(script)
            if (script.x >= 0 and script.x < 100 and script.y >= 0 and script.y < 200):
                self.squares[script.y][script.x].addscript(script)
            return True
        except FirstItemLoadException, e:
            return False

    def delscript(self, x, y, idx):
        """ Deletes a mapscript, both from the associated square, and our internal list. """
        square = self.squares[y][x]
        script = square.scripts[idx]
        if (script is not None):
            self.scripts.remove(script)
            self.squares[y][x].delscript(script)

    def addentity(self):
        """ Add an entity. """
        try:
            entity = Entity.new(c.book, self.is_savegame())
            entity.read(self.df_ent)
            self.entities.append(entity)
            if (entity.x >= 0 and entity.x < 100 and entity.y >= 0 and entity.y < 200):
                self.squares[entity.y][entity.x].addentity(entity)
            return True
        except FirstItemLoadException, e:
            return False

    def delentity(self, x, y):
        """ Deletes an entity, both from the associated square, and our internal list. """
        square = self.squares[y][x]
        ent = square.entity
        if (ent is not None):
            self.entities.remove(ent)
            square.delentity()

    def rgb_color(self):
        return (self.color_r << 24) + (self.color_g << 16) + (self.color_b << 8) + (0xFF)

    def coords_relative(self, x, y, dir):
        """
        Static method to return coordinates for the square
        relative to the given coords.  1 = N, 2 = NE, etc
        """
        if (dir == self.DIR_N):
            if (y < 2):
                return None
            else:
                return (x, y-2)
        elif (dir == self.DIR_NE):
            if ((y % 2) == 0):
                if (y > 0):
                    return (x, y-1)
                else:
                    return None
            elif (x < 99):
                return (x+1, y-1)
            else:
                return None
        elif (dir == self.DIR_E):
            if (x < 99):
                return (x+1, y)
            else:
                return None
        elif (dir == self.DIR_SE):
            if ((y % 2) == 0):
                return (x, y+1)
            elif (x < 99 and y < 199):
                return (x+1, y+1)
            else:
                return None
        elif (dir == self.DIR_S):
            if (y < 198):
                return (x, y+2)
            else:
                return None
        elif (dir == self.DIR_SW):
            if ((y % 2) == 1):
                if (y < 199):
                    return (x, y+1)
                else:
                    return None
            elif (x > 0):
                return (x-1, y+1)
            else:
                return None
        elif (dir == self.DIR_W):
            if (x > 1):
                return (x-1, y)
            else:
                return None
        elif (dir == self.DIR_NW):
            if ((y % 2) == 1):
                return (x, y-1)
            elif (y > 0 and x > 0):
                return (x-1, y-1)
            else:
                return None
        else:
            return None

    def square_relative(self, x, y, dir):
        """ Returns a square object relative to the given coords. """
        coords = self.coords_relative(x, y, dir)
        if (coords):
            return self.squares[coords[1]][coords[0]]
        else:
            return None

    @staticmethod
    def load(filename, book=None, req_book=None):
        """
        Static method to load a map file.  This will open the file once
        and read in a bit of data to determine whether this is a Book 1 map file
        or a Book 1 map file, and then call the appropriate constructor and
        return the object.
        """
        df = Savefile(filename)

        # Both B1 and B2 map files start with nine strings (though their meanings
        # vary) - at that point, Book 2 goes into some integer data whereas Book
        # 1 has a couple more strings.  The first two binary bytes in Book 2 seem
        # to each *always* be 0x01, so that's how we'll differentiate
        if book is None:
            try:
                df.open_r()
                for i in range(9):
                    df.readstr()
                c1 = df.readuchar()
                c2 = df.readuchar()
                df.close()
            except (IOError, struct.error), e:
                raise LoadException(str(e))

            if c1 == 1 or c2 == 1:
                book = 2
            else:
                book = 1

        # See if we're required to conform to a specific book
        if (req_book is not None and book != req_book):
            raise LoadException('This utility can only load Book %d map files; this file is from Book %d' % (req_book, book))

        # Now actually return the object
        if book == 1:
            c.switch_to_book(1)
            return B1Map(df)
        else:
            c.switch_to_book(2)
            return B2Map(df)

class B1Map(Map):
    """
    Book 1 Map definitions
    """

    book = 1

    def __init__(self, df):

        # Book 1-specific vars
        self.mapid = -1
        self.exit_north = ''
        self.exit_east = ''
        self.exit_south = ''
        self.exit_west = ''
        self.parallax_1 = -1
        self.parallax_2 = -1
        self.clouds = -1
        self.savegame_1 = -1
        self.savegame_2 = -1
        self.savegame_3 = -1
        self.map_unknownh1 = -1

        # Base class attributes
        super(B1Map, self).__init__(df)

    def read(self):
        """ Read in the whole map from a file descriptor. """

        try:

            # Open the file
            self.df.open_r()

            # Start processing
            self.mapid = self.df.readstr()
            self.mapname = self.df.readstr()
            self.soundfile1 = self.df.readstr()
            self.soundfile2 = self.df.readstr()
            self.exit_north = self.df.readstr()
            self.exit_east = self.df.readstr()
            self.exit_south = self.df.readstr()
            self.exit_west = self.df.readstr()
            self.skybox = self.df.readstr()
            self.soundfile3 = self.df.readstr()
            self.map_unknowni1 = self.df.readint()
            self.map_unknownh1 = self.df.readshort()

            self.color_r = self.df.readuchar()
            self.color_g = self.df.readuchar()
            self.color_b = self.df.readuchar()
            self.color_a = self.df.readuchar()

            self.parallax_1 = self.df.readint()
            self.parallax_2 = self.df.readint()
            self.clouds = self.df.readint()
            self.savegame_1 = self.df.readint()
            self.savegame_2 = self.df.readint()
            self.savegame_3 = self.df.readint()

            # Squares
            self.set_square_savegame()
            for i in range(200*100):
                self.addsquare()

            # Scripts...  Just keep going until EOF
            try:
                while (self.addscript()):
                    pass
            except FirstItemLoadException, e:
                pass

            # Entities...  Just keep going until EOF (note that this is in a separate file)
            # Also note that we have to support situations where there is no entity file
            if (self.df_ent.exists()):
                self.df_ent.open_r()
                try:
                    while (self.addentity()):
                        pass
                except FirstItemLoadException, e:
                    pass
                self.df_ent.close()

            # If there's extra data at the end, we likely don't have
            # a valid char file
            self.extradata = self.df.read()
            if (len(self.extradata)>0):
                raise LoadException('Extra data at end of file')

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
        self.df.writestr(self.soundfile2)
        self.df.writestr(self.exit_north)
        self.df.writestr(self.exit_east)
        self.df.writestr(self.exit_south)
        self.df.writestr(self.exit_west)
        self.df.writestr(self.skybox)
        self.df.writestr(self.soundfile3)
        self.df.writeint(self.map_unknowni1)
        self.df.writeshort(self.map_unknownh1)
        self.df.writeuchar(self.color_r)
        self.df.writeuchar(self.color_g)
        self.df.writeuchar(self.color_b)
        self.df.writeuchar(self.color_a)
        self.df.writeint(self.parallax_1)
        self.df.writeint(self.parallax_2)
        self.df.writeint(self.clouds)
        self.df.writeint(self.savegame_1)
        self.df.writeint(self.savegame_2)
        self.df.writeint(self.savegame_3)

        # Squares
        for row in self.squares:
            for square in row:
                square.write(self.df)

        # Scripts
        for script in self.scripts:
            script.write(self.df)

        # Any extra data we might have
        if (len(self.extradata) > 0):
            self.df.writestr(self.extradata)

        # Clean up
        self.df.close()

        # Now write out entities, which actually happens in a different file
        # We open regardless of entities, because we'd have to zero out the
        # file.
        self.set_df_ent()
        self.df_ent.open_w()
        for entity in self.entities:
            entity.write(self.df_ent)
        self.df_ent.close()

    def is_global(self):
        return (self.savegame_1 == 0 and self.savegame_2 == 0 and self.savegame_3 == 0)

    def is_savegame(self):
        return not self.is_global()
        # ... On the Greenhouse and direct-from-Basilisk versions, the savegame map files have
        # always had "666" in these values for me.  On at least one Steam version, it looks
        # like the first value is 320, so we're just going to invert is_global() instead.
        # Which is really what we should have been doing anyway, but whatever.
        # Savegames are... evil?  I guess?
        #return (self.savegame_1 == 666 and self.savegame_2 == 666 and self.savegame_3 == 666)

    def _sub_replicate(self, newmap):
        """
        Replicate b1-specific vars
        """
        newmap.mapid = self.mapid
        newmap.exit_north = self.exit_north
        newmap.exit_east = self.exit_east
        newmap.exit_south = self.exit_south
        newmap.exit_west = self.exit_west
        newmap.parallax_1 = self.parallax_1
        newmap.parallax_2 = self.parallax_2
        newmap.clouds = self.clouds
        newmap.savegame_1 = self.savegame_1
        newmap.savegame_2 = self.savegame_2
        newmap.savegame_3 = self.savegame_3
        newmap.map_unknownh1 = self.map_unknownh1

class B2Map(Map):
    """
    Book 2 Map definitions
    """

    book = 2

    def __init__(self, df):

        # Book 2 specific vars
        self.openingscript = ''
        self.map_unknownstr1 = ''
        self.map_unknownstr2 = ''
        self.soundfile4 = ''
        self.map_unknownc1 = -1
        self.map_unknownc2 = -1
        self.random_entity_1 = -1
        self.random_entity_2 = -1
        self.map_unknowni2 = -1
        self.map_flags = -1
        self.map_unknowni4 = -1
        self.map_unknownc5 = -1
        self.map_unknownc6 = -1
        self.map_unknownc7 = -1
        self.map_unknownc8 = -1
        self.map_unknownstr4 = ''
        self.map_unknownstr5 = ''
        self.map_unknownstr6 = ''

        # Now the base attributes
        super(B2Map, self).__init__(df)

    def read(self):
        """ Read in the whole map from a file descriptor. """

        try:

            # Open the file
            self.df.open_r()

            # Start processing
            self.mapname = self.df.readstr()
            self.openingscript = self.df.readstr()
            self.map_unknownstr1 = self.df.readstr()
            self.map_unknownstr2 = self.df.readstr()
            self.skybox = self.df.readstr()
            self.soundfile1 = self.df.readstr()
            self.soundfile2 = self.df.readstr()
            self.soundfile3 = self.df.readstr()
            self.soundfile4 = self.df.readstr()
            self.map_unknownc1 = self.df.readuchar()
            self.map_unknownc2 = self.df.readuchar()
            self.random_entity_1 = self.df.readuchar()
            self.random_entity_2 = self.df.readuchar()
            self.color_r = self.df.readuchar()
            self.color_g = self.df.readuchar()
            self.color_b = self.df.readuchar()
            self.color_a = self.df.readuchar()
            # map_unknowni1 looks like it may contain parallax values
            self.map_unknowni1 = self.df.readint()
            self.map_unknowni2 = self.df.readint()
            self.map_flags = self.df.readint()
            self.map_unknowni4 = self.df.readint()
            self.tree_set = self.df.readint()

            # These are all zero on the "global" map files
            self.map_unknownc5 = self.df.readuchar()
            self.map_unknownc6 = self.df.readuchar()
            self.map_unknownc7 = self.df.readuchar()
            self.map_unknownc8 = self.df.readuchar()

            self.map_unknownstr4 = self.df.readstr()
            self.map_unknownstr5 = self.df.readstr()
            self.map_unknownstr6 = self.df.readstr()

            # Squares
            self.set_square_savegame()
            for i in range(200*100):
                self.addsquare()

            # Scripts...  Just keep going until EOF
            try:
                while (self.addscript()):
                    pass
            except FirstItemLoadException, e:
                pass

            # Entities...  Just keep going until EOF (note that this is in a separate file)
            # Also note that we have to support situations where there is no entity file
            if (self.df_ent.exists()):
                self.df_ent.open_r()
                try:
                    while (self.addentity()):
                        pass
                except FirstItemLoadException, e:
                    pass
                self.df_ent.close()

            # If there's extra data at the end, we likely don't have
            # a valid char file
            self.extradata = self.df.read()
            if (len(self.extradata)>0):
                raise LoadException('Extra data at end of file')

            # Close the file
            self.df.close()

        except (IOError, struct.error), e:
            raise LoadException(str(e))

    def write(self):
        """ Writes out the map to the file descriptor. """
        
        # Open the file
        self.df.open_w()

        # Start
        self.df.writestr(self.mapname)
        self.df.writestr(self.openingscript)
        self.df.writestr(self.map_unknownstr1)
        self.df.writestr(self.map_unknownstr2)
        self.df.writestr(self.skybox)
        self.df.writestr(self.soundfile1)
        self.df.writestr(self.soundfile2)
        self.df.writestr(self.soundfile3)
        self.df.writestr(self.soundfile4)
        self.df.writeuchar(self.map_unknownc1)
        self.df.writeuchar(self.map_unknownc2)
        self.df.writeuchar(self.random_entity_1)
        self.df.writeuchar(self.random_entity_2)
        self.df.writeuchar(self.color_r)
        self.df.writeuchar(self.color_g)
        self.df.writeuchar(self.color_b)
        self.df.writeuchar(self.color_a)
        self.df.writeint(self.map_unknowni1)
        self.df.writeint(self.map_unknowni2)
        self.df.writeint(self.map_flags)
        self.df.writeint(self.map_unknowni4)
        self.df.writeint(self.tree_set)
        self.df.writeuchar(self.map_unknownc5)
        self.df.writeuchar(self.map_unknownc6)
        self.df.writeuchar(self.map_unknownc7)
        self.df.writeuchar(self.map_unknownc8)
        self.df.writestr(self.map_unknownstr4)
        self.df.writestr(self.map_unknownstr5)
        self.df.writestr(self.map_unknownstr6)

        # Squares
        for row in self.squares:
            for square in row:
                square.write(self.df)

        # Scripts
        for script in self.scripts:
            script.write(self.df)

        # Any extra data we might have
        if (len(self.extradata) > 0):
            self.df.writestr(self.extradata)

        # Clean up
        self.df.close()

        # Now write out entities, which actually happens in a different file
        # We open regardless of entities, because we'd have to zero out the
        # file.
        self.set_df_ent()
        self.df_ent.open_w()
        for entity in self.entities:
            entity.write(self.df_ent)
        self.df_ent.close()

    def is_global(self):
        return (self.map_unknownc5 == 0 and self.map_unknownc6 == 0 and self.map_unknownc7 == 0)

    def is_savegame(self):
        return not self.is_global()
        #return (self.map_unknownc5 != 0 or self.map_unknownc6 != 0 or self.map_unknownc7 != 0)

    def _sub_replicate(self, newmap):
        """
        Replicate b2-specific vars
        """
        newmap.openingscript = self.openingscript
        newmap.map_unknownstr1 = self.map_unknownstr1
        newmap.map_unknownstr2 = self.map_unknownstr2
        newmap.soundfile4 = self.soundfile4
        newmap.map_unknownc1 = self.map_unknownc1
        newmap.map_unknownc2 = self.map_unknownc2
        newmap.random_entity_1 = self.random_entity_1
        newmap.random_entity_2 = self.random_entity_2
        newmap.map_unknowni2 = self.map_unknowni2
        newmap.map_flags = self.map_flags
        newmap.map_unknowni4 = self.map_unknowni4
        newmap.map_unknownc5 = self.map_unknownc5
        newmap.map_unknownc6 = self.map_unknownc6
        newmap.map_unknownc7 = self.map_unknownc7
        newmap.map_unknownc8 = self.map_unknownc8
        newmap.map_unknownstr4 = self.map_unknownstr4
        newmap.map_unknownstr5 = self.map_unknownstr5
        newmap.map_unknownstr6 = self.map_unknownstr6
