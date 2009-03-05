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

import os
import struct
from eschalonb1.savefile import Savefile, LoadException, FirstItemLoadException
from eschalonb1.square import Square
from eschalonb1.mapscript import Mapscript
from eschalonb1.entity import Entity

class Map:
    """ The base Map class.  """

    def __init__(self, filename):
        """ A fresh object. """

        # Everything else follows...
        self.df = None
        self.df_ent = None
        self.filename_ent = ''
        self.mapid = ''
        self.mapname = ''
        self.soundfile1 = ''
        self.soundfile2 = ''
        self.exit_north = ''
        self.exit_east = ''
        self.exit_south = ''
        self.exit_west = ''
        self.skybox = ''
        self.soundfile3 = ''
        self.unknowni1 = -1
        self.unknownh1 = -1

        # This is pure supposition at this point, but it seems to fit
        self.color_r = -1
        self.color_g = -1
        self.color_b = -1
        self.color_a = -1

        self.parallax_1 = -1
        self.parallax_2 = -1
        self.unknowni4 = -1
        self.savegame_1 = -1
        self.savegame_2 = -1
        self.savegame_3 = -1

        self.extradata = ''

        self.cursqcol = 0
        self.cursqrow = 0

        self.squares = []
        for i in range(200):
            self.squares.append([])
            for j in range(100):
                self.squares[i].append(Square())

        self.scripts = []
        self.entities = []

        self.df = Savefile(filename)
        self.set_df_ent()

    def set_df_ent(self):
        self.df_ent = Savefile(self.df.filename[:self.df.filename.rindex('.map')] + '.ent')

    def is_global(self):
        return (self.savegame_1 == 0 and self.savegame_2 == 0 and self.savegame_3 == 0)

    def is_savegame(self):
        # Savegames are... evil?  I guess?
        return (self.savegame_1 == 666 and self.savegame_2 == 666 and self.savegame_3 == 666)

    def replicate(self):
        # Note that this could, theoretically, lead to contention issues, since
        # Savefile doesn't as yet lock the file.  So, er, be careful for now, I
        # guess.
        newmap = Map(self.df.filename)

        # Single vals (no need to do actual replication)
        newmap.mapid = self.mapid
        newmap.mapname = self.mapname
        newmap.soundfile1 = self.soundfile1
        newmap.soundfile2 = self.soundfile2
        newmap.exit_north = self.exit_north
        newmap.exit_east = self.exit_east
        newmap.exit_south = self.exit_south
        newmap.exit_west = self.exit_west
        newmap.skybox = self.skybox
        newmap.soundfile3 = self.soundfile3
        newmap.unknowni1 = self.unknowni1
        newmap.unknownh1 = self.unknownh1
        newmap.color_r = self.color_r
        newmap.color_g = self.color_g
        newmap.color_b = self.color_b
        newmap.color_a = self.color_a
        newmap.parallax_1 = self.parallax_1
        newmap.parallax_2 = self.parallax_2
        newmap.unknowni4 = self.unknowni4
        newmap.savegame_1 = self.savegame_1
        newmap.savegame_2 = self.savegame_2
        newmap.savegame_3 = self.savegame_3
        newmap.extradata = self.extradata

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

    def addscript(self):
        """ Add a mapscript. """
        try:
            script = Mapscript(self.is_savegame())
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
            entity = Entity(self.is_savegame())
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
            self.unknowni1 = self.df.readint()
            self.unknownh1 = self.df.readshort()

            self.color_r = self.df.readuchar()
            self.color_g = self.df.readuchar()
            self.color_b = self.df.readuchar()
            self.color_a = self.df.readuchar()

            self.parallax_1 = self.df.readint()
            self.parallax_2 = self.df.readint()
            self.unknowni4 = self.df.readint()
            self.savegame_1 = self.df.readint()
            self.savegame_2 = self.df.readint()
            self.savegame_3 = self.df.readint()

            # Squares
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
                # TODO: We should except here, but until we get it figured out, we won't
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
        self.df.writeint(self.unknowni1)
        self.df.writeshort(self.unknownh1)
        self.df.writeuchar(self.color_r)
        self.df.writeuchar(self.color_g)
        self.df.writeuchar(self.color_b)
        self.df.writeuchar(self.color_a)
        self.df.writeint(self.parallax_1)
        self.df.writeint(self.parallax_2)
        self.df.writeint(self.unknowni4)
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
            

    def rgb_color(self):
        return (self.color_r << 24) + (self.color_g << 16) + (self.color_b << 8) + (0xFF)

