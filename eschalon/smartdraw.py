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

import random
from eschalonb1.map import Map

class SmartDraw(object):
    """ A class to deal with "smart" drawing functions. """

    CONN_NE = 0x01
    CONN_SE = 0x02
    CONN_SW = 0x04
    CONN_NW = 0x08
    CONN_N = 0x10
    CONN_E = 0x20
    CONN_S = 0x40
    CONN_W = 0x80

    REV_CONN = {
            CONN_NE: CONN_SW,
            CONN_SE: CONN_NW,
            CONN_SW: CONN_NE,
            CONN_NW: CONN_SE,
            CONN_N: CONN_S,
            CONN_E: CONN_W,
            CONN_S: CONN_N,
            CONN_W: CONN_E
        }

    ADJ_CONN = {
            CONN_NE: CONN_N|CONN_E,
            CONN_SE: CONN_S|CONN_E,
            CONN_SW: CONN_S|CONN_W,
            CONN_NW: CONN_N|CONN_W,
            CONN_N: CONN_NE|CONN_NW,
            CONN_E: CONN_NE|CONN_SE,
            CONN_S: CONN_SE|CONN_SW,
            CONN_W: CONN_NW|CONN_SW
        }

    IDX_WALL = 0
    IDX_FENCE = 1
    IDX_GRASS = 2

    def __init__(self):
        self.wallstarts = [161, 171, 181, 191, 201]
        self.fencestart = 73
        self.special = 213
        self.grass_tiles = [9, 10, 11, 12]
        self.map = None

        # One empty dict for each IDX_*
        self.indexes = [ {}, {}, {} ]
        self.revindexes = [ {}, {}, {} ]

        # Wall Indexes
        self.add_index(self.IDX_WALL, -1, self.CONN_NE|self.CONN_SE|self.CONN_SW|self.CONN_NW)
        self.add_index(self.IDX_WALL, 0, self.CONN_NE|self.CONN_SW)
        self.add_index(self.IDX_WALL, 1, self.CONN_SE|self.CONN_NW)
        self.add_index(self.IDX_WALL, 2, self.CONN_SE|self.CONN_SW)
        self.add_index(self.IDX_WALL, 3, self.CONN_SW|self.CONN_NW)
        self.add_index(self.IDX_WALL, 4, self.CONN_NE|self.CONN_NW)
        self.add_index(self.IDX_WALL, 5, self.CONN_NE|self.CONN_SE)
        self.add_index(self.IDX_WALL, 6, self.CONN_SE|self.CONN_SW|self.CONN_NW)
        self.add_index(self.IDX_WALL, 7, self.CONN_NE|self.CONN_SW|self.CONN_NW)
        self.add_index(self.IDX_WALL, 8, self.CONN_NE|self.CONN_SE|self.CONN_NW)
        self.add_index(self.IDX_WALL, 9, self.CONN_NE|self.CONN_SE|self.CONN_SW)

        # Fence Indexes
        self.add_index(self.IDX_FENCE, 0, self.CONN_NE|self.CONN_SW)
        self.add_index(self.IDX_FENCE, 1, self.CONN_SE|self.CONN_NW)
        self.add_index(self.IDX_FENCE, 2, self.CONN_SW|self.CONN_SE)
        self.add_index(self.IDX_FENCE, 3, self.CONN_NW|self.CONN_SW)
        self.add_index(self.IDX_FENCE, 4, self.CONN_NE|self.CONN_NW)
        self.add_index(self.IDX_FENCE, 5, self.CONN_SE|self.CONN_NE)

        # Grass Indexes
        self.add_index(self.IDX_GRASS, 97, self.CONN_SE)
        self.add_index(self.IDX_GRASS, 98, self.CONN_SW)
        self.add_index(self.IDX_GRASS, 99, self.CONN_NW)
        self.add_index(self.IDX_GRASS, 100, self.CONN_NE)
        self.add_index(self.IDX_GRASS, 101, self.CONN_SE|self.CONN_SW)
        self.add_index(self.IDX_GRASS, 102, self.CONN_NW|self.CONN_NE)
        self.add_index(self.IDX_GRASS, 103, self.CONN_SW|self.CONN_NW)
        self.add_index(self.IDX_GRASS, 104, self.CONN_NE|self.CONN_SE)
        self.add_index(self.IDX_GRASS, 105, self.CONN_SE|self.CONN_NW)
        self.add_index(self.IDX_GRASS, 106, self.CONN_NE|self.CONN_SW)
        self.add_index(self.IDX_GRASS, 107, self.CONN_N)
        self.add_index(self.IDX_GRASS, 108, self.CONN_S)
        self.add_index(self.IDX_GRASS, 109, self.CONN_W)
        self.add_index(self.IDX_GRASS, 110, self.CONN_E)
        self.add_index(self.IDX_GRASS, 126, self.CONN_N|self.CONN_S)
        self.add_index(self.IDX_GRASS, 143, self.CONN_W|self.CONN_E)
        self.add_index(self.IDX_GRASS, 157, self.CONN_W|self.CONN_SE)
        self.add_index(self.IDX_GRASS, 158, self.CONN_N|self.CONN_SW)
        self.add_index(self.IDX_GRASS, 159, self.CONN_E|self.CONN_NW)
        self.add_index(self.IDX_GRASS, 160, self.CONN_W|self.CONN_NE)
        self.add_index(self.IDX_GRASS, 161, self.CONN_E|self.CONN_SW|self.CONN_NW)
        self.add_index(self.IDX_GRASS, 162, self.CONN_W|self.CONN_NE|self.CONN_SE)
        self.add_index(self.IDX_GRASS, 163, self.CONN_N|self.CONN_SE)
        self.add_index(self.IDX_GRASS, 164, self.CONN_E|self.CONN_SW)
        self.add_index(self.IDX_GRASS, 165, self.CONN_S|self.CONN_NW)
        self.add_index(self.IDX_GRASS, 166, self.CONN_S|self.CONN_NE)
        self.add_index(self.IDX_GRASS, 167, self.CONN_N|self.CONN_SE|self.CONN_SW)
        self.add_index(self.IDX_GRASS, 168, self.CONN_S|self.CONN_NW|self.CONN_NE)

        # Pool to randomly choose from if we're completely surrounded by grass
        self.grass_fullest = [161, 162, 167, 168]

    def add_index(self, idxnum, index, connections):
        self.indexes[idxnum][index] = connections
        self.revindexes[idxnum][connections] = index

    def set_map(self, map):
        self.map = map

    def set_special(self, wallid):
        self.special = wallid

    def get_wall_group(self, square, wallgroup=None):
        """
        Returns the base group ID of the given wall ID.
        If appropriate (ie: for checking adjacent walls while editing, pass in
        the wallgroup you're working with, and this will return that group if
        the "special" 4-connection object is found.
        """
        wallstart = -1
        if (wallgroup is not None and square.wallimg == self.special):
            return wallgroup
        for start in self.wallstarts:
            if (square.wallimg >= start and square.wallimg < start+10):
                return start
        if (square.wallimg >= self.fencestart and square.wallimg < self.fencestart+6):
            return self.fencestart
        return None

    def draw_wall(self, square):
        """
        Draws using the given wall.
        Will return a list of squares that have been updated by this action
        (not including the given square, which is assumed), or None if smart
        drawing isn't applicable in this case.
        """
        # First set up and make sure that we're even drawing a wall
        retarr = []
        wallgroup = self.get_wall_group(square)
        if (wallgroup is None):
            return None

        # Fences act similarly, but different enough that I think things would
        # be problematic if I were to try to handle everything in one function
        # here.
        if (wallgroup == self.fencestart):
            return self.draw_fence(square)

        # Now loop through our directions and see where we should link to.
        # We'll additionally call out to add_wall_connection() where appropriate
        # to update adjacent walls.
        connflags = 0
        flagcount = 0
        for (mapdir, conndir) in zip(
                [Map.DIR_NE, Map.DIR_SE, Map.DIR_SW, Map.DIR_NW],
                [self.CONN_NE, self.CONN_SE, self.CONN_SW, self.CONN_NW]):
            adjsquare = self.map.square_relative(square.x, square.y, mapdir)
            adjgroup = self.get_wall_group(adjsquare, wallgroup)
            if (adjgroup is None or adjgroup != wallgroup):
                continue
            connflags = connflags|conndir
            flagcount += 1
            if (self.add_wall_connection(wallgroup, adjsquare, self.REV_CONN[conndir])):
                retarr.append(adjsquare)

        # Figure out what to put down if we don't actually have a match
        if (connflags not in self.revindexes[self.IDX_WALL]):
            if (flagcount == 0):
                connflags = self.indexes[self.IDX_WALL][0]
            elif (flagcount == 1):
                if ((connflags & self.CONN_NE) == self.CONN_NE or
                    (connflags & self.CONN_SW) == self.CONN_SW):
                    connflags = self.indexes[self.IDX_WALL][0]
                else:
                    connflags = self.indexes[self.IDX_WALL][1]
            else:
                raise Exception("flagcount isn't 1 or 0 - should figure out why")

        # TODO: this is duplicated in add_wall_connection...
        if (self.revindexes[self.IDX_WALL][connflags] == -1):
            square.wallimg = self.special
        else:
            square.wallimg = wallgroup + self.revindexes[self.IDX_WALL][connflags]

        # And lastly, return.
        return retarr

    def add_wall_connection(self, group, square, dir):
        """
        Adds a connection to the given square.  Note that this doesn't do
        any actual bounds checking; it should really only be called from
        draw_wall(), above.  Returns whether or not we modified the square.

        It *does* however "clean" squares, to prune off connections which
        don't need to be there anymore.

        There's some duplicated code in here from draw_wall(), but it's
        different enough that I don't think it makes sense to combine the two.
        """

        # First grab our current status and add in the requested connection
        if (square.wallimg == self.special):
            idx = -1
        else:
            idx = square.wallimg - group
        curflags = self.indexes[self.IDX_WALL][idx]
        newflags = dir

        # Now prune any connections which shouldn't be active, skipping the
        # direction that we were just told to add
        conncount = 0
        for (mapdir, conndir) in zip(
                [Map.DIR_NE, Map.DIR_SE, Map.DIR_SW, Map.DIR_NW],
                [self.CONN_NE, self.CONN_SE, self.CONN_SW, self.CONN_NW]):
            if (conndir == dir):
                continue
            testsquare = self.map.square_relative(square.x, square.y, mapdir)
            testgroup = self.get_wall_group(testsquare, group)
            if (testgroup and testgroup == group):
                conncount += 1
                newflags = (newflags | conndir)

        # Now clean up.  If there were no connections found, just use the
        # appropriate straight tile.  If 1, just add in our connection.
        # Otherwise, accept the pruning.
        if (conncount == 0):
            if (dir == self.CONN_NE or dir == self.CONN_SW):
                newflags = self.CONN_NE|self.CONN_SW
            else:
                newflags = self.CONN_NW|self.CONN_SE

        # Now after all that, see if we even changed at all.  If so,
        # make the change and report back.
        if (curflags == newflags):
            return False
        else:
            if (self.revindexes[self.IDX_WALL][newflags] == -1):
                square.wallimg = self.special
            else:
                square.wallimg = group + self.revindexes[self.IDX_WALL][newflags]
            return True

    def draw_fence(self, square):
        """
        Draws a fence.  If we've got here, we KNOW that we're a fence already.
        Note that there's a lot of duplicate code from draw_wall(), above, but
        there's enough differences that I'd rather not combine the two.

        Will return a list of squares that have been updated by this action
        (not including the given square, which is assumed).
        """

        retarr = []

        # Now loop through our directions and see where we should link to.
        # We'll additionally call out to add_fence_connection() where appropriate
        # to update adjacent walls.  We're hampered a bit since each fence square
        # can only support two connections.
        connflags = 0
        flagcount = 0
        for (mapdir, conndir) in zip(
                [Map.DIR_NE, Map.DIR_SE, Map.DIR_SW, Map.DIR_NW],
                [self.CONN_NE, self.CONN_SE, self.CONN_SW, self.CONN_NW]):
            adjsquare = self.map.square_relative(square.x, square.y, mapdir)
            adjgroup = self.get_wall_group(adjsquare)
            if (adjgroup is None or adjgroup != self.fencestart):
                continue
            connflags = connflags|conndir
            flagcount += 1
            if (self.add_fence_connection(adjsquare, self.REV_CONN[conndir])):
                retarr.append(adjsquare)
            if (flagcount == 2):
                break

        # Figure out what to put down if we don't actually have a match
        if (connflags not in self.revindexes[self.IDX_FENCE]):
            if (flagcount == 0):
                connflags = self.indexes[self.IDX_FENCE][0]
            elif (flagcount == 1):
                if ((connflags & self.CONN_NE) == self.CONN_NE or
                    (connflags & self.CONN_SW) == self.CONN_SW):
                    connflags = self.indexes[self.IDX_FENCE][0]
                else:
                    connflags = self.indexes[self.IDX_FENCE][1]
            else:
                raise Exception("flagcount isn't 1 or 0 - should figure out why")

        square.wallimg = self.fencestart + self.revindexes[self.IDX_FENCE][connflags]

        # And lastly, return.
        return retarr

    def add_fence_connection(self, square, dir):
        """
        Adds a connection to the given square.  Note that this doesn't do
        any actual bounds checking; it should really only be called from
        draw_fence(), above.  Returns whether or not we modified the square.

        It *does* however "clean" squares, to prune off connections which
        don't need to be there anymore.

        There's some duplicated code in here from draw_fence(), but it's
        different enough that I don't think it makes sense to combine the two.

        Again, the disclaimer from draw_fence() about duplication applies.
        """

        # First grab our current status and add in the requested connection
        idx = square.wallimg - self.fencestart
        curflags = self.indexes[self.IDX_FENCE][idx]
        newflags = dir

        # Now prune any connections which shouldn't be active, skipping the
        # direction that we were just told to add.  Note that we're stopping
        # after the first one we find.
        conncount = 0
        for (mapdir, conndir) in zip(
                [Map.DIR_NE, Map.DIR_SE, Map.DIR_SW, Map.DIR_NW],
                [self.CONN_NE, self.CONN_SE, self.CONN_SW, self.CONN_NW]):
            if (conndir == dir):
                continue
            testsquare = self.map.square_relative(square.x, square.y, mapdir)
            testgroup = self.get_wall_group(testsquare)
            if (testgroup and testgroup == self.fencestart):
                conncount += 1
                newflags = (newflags | conndir)
                break

        # Now clean up.  If there were no connections found, just use the
        # appropriate straight tile.  If 1, just add in our connection.
        # Otherwise, accept the pruning.
        if (conncount == 0):
            if (dir == self.CONN_NE or dir == self.CONN_SW):
                newflags = self.CONN_NE|self.CONN_SW
            else:
                newflags = self.CONN_NW|self.CONN_SE

        # Now after all that, see if we even changed at all.  If so,
        # make the change and report back.
        if (curflags == newflags):
            return False
        else:
            square.wallimg = self.fencestart + self.revindexes[self.IDX_FENCE][newflags]
            return True

    def draw_floor(self, square):
        """
        Handles drawing a floor.  This should just be decal work.
        Returns a list of squares that have been updated by this action
        (not including the given square, which is assumed.
        """
        # TODO: We probably only want to overwrite decals that we would
        # have put in place; not other decals
        # TODO: Single squares of water in the middle of other terrain
        # should be not a wall
        if (square.floorimg in self.grass_tiles):
            # TODO: handle adjacent tiles
            # Clear out our decal if it's redundant
            if (square.decalimg in self.indexes[self.IDX_GRASS].keys()):
                square.decalimg = 0
            return []
        else:
            return self.process_grass_decals(square)

    def process_grass_decals(self, square, recurse=True, known={}):
        """
        Given a square, figure out what kind of grass decals it should have,
        if any.  Will actually set the decal image, as well.  If 'recurse'
        is True, we'll make recursive calls to do the same with adjacent
        squares.  Using 'known' you can pass in any squares which may have
        already been loaded (which can help avoid unnecessary calls to
        Map.square_relative().
        
        Returns a list of modified squares if we're recursing, or just
        true/false otherwise.
        """
        connflags = 0
        connflags_not = 0
        flagcount = 0
        affected = []
        curdecal = square.decalimg

        # First find out more-typical adjacent squares
        for (mapdir, conndir) in zip(
                [Map.DIR_NE, Map.DIR_SE, Map.DIR_SW, Map.DIR_NW],
                [self.CONN_NE, self.CONN_SE, self.CONN_SW, self.CONN_NW]):
            if (conndir in known):
                connflags_not = connflags_not|conndir
                continue
            else:
                adjsquare = self.map.square_relative(square.x, square.y, mapdir)
                if (not adjsquare):
                    continue
            if (adjsquare.floorimg in self.grass_tiles):
                connflags = connflags|conndir
                flagcount += 1
            else:
                connflags_not = connflags_not|conndir

            # Process adjacent squares if we're supposed to
            if (recurse):
                if (adjsquare.floorimg not in self.grass_tiles):
                    if (self.process_grass_decals(adjsquare, False, { self.REV_CONN[conndir]: square })):
                        affected.append(adjsquare)

        # If we're recursing, we'll need to check the cardinal directions as
        # well, to clear out errant corner-connection decals
        # TODO: We should really just grab all these at the beginning and
        # cache them.
        if (recurse):
            for (mapdir, conndir) in zip(
                    [Map.DIR_N, Map.DIR_E, Map.DIR_S, Map.DIR_W],
                    [self.CONN_N, self.CONN_E, self.CONN_S, self.CONN_W]):
                adjsquare = self.map.square_relative(square.x, square.y, mapdir)
                if (not adjsquare):
                    continue
                if (adjsquare.floorimg not in self.grass_tiles):
                    if (self.process_grass_decals(adjsquare, False, { self.REV_CONN[conndir]: square })):
                        affected.append(adjsquare)

        # Now refine the list
        if (flagcount > 2):

            # If we're this full, just pull from our "fullest" list
            # instead
            if (flagcount == 4):
                # Just pick a random one from our "fullest" pool
                square.decalimg = random.choice(self.grass_fullest)
            elif (flagcount == 3):
                # Pick one from the "fullest" pool which matches
                # most closely
                for choice in self.grass_fullest:
                    choiceflags = self.indexes[self.IDX_GRASS][choice]
                    if ((choiceflags & connflags_not) == 0):
                        square.decalimg = choice
                        break

            # Prune, in case there are adjacent tiles
            curflags = self.indexes[self.IDX_GRASS][square.decalimg]
            for (mapdir, conndir) in zip(
                    [Map.DIR_N, Map.DIR_E, Map.DIR_S, Map.DIR_W],
                    [self.CONN_N, self.CONN_E, self.CONN_S, self.CONN_W]):
                adjsquare = self.map.square_relative(square.x, square.y, mapdir)
                if (not adjsquare):
                    continue
                if (adjsquare.floorimg not in self.grass_tiles):
                    curflags = (curflags & ~conndir)
            if (curflags in self.revindexes[self.IDX_GRASS]):
                square.decalimg = self.revindexes[self.IDX_GRASS][curflags]
        else:
            # See if there's a more-specific tile we could match on
            for (mapdir, conndir) in zip(
                    [Map.DIR_N, Map.DIR_E, Map.DIR_S, Map.DIR_W],
                    [self.CONN_N, self.CONN_E, self.CONN_S, self.CONN_W]):
                if (connflags & self.ADJ_CONN[conndir] == 0):
                    continue
                if ((connflags|conndir) in self.revindexes[self.IDX_GRASS]):
                    adjsquare = self.map.square_relative(square.x, square.y, mapdir)
                    if (not adjsquare):
                        continue
                    if (adjsquare.floorimg in self.grass_tiles):
                        connflags = connflags | conndir
                        if (flagcount != 0):
                            break
            if (connflags == 0):
                if (square.decalimg in self.indexes[self.IDX_GRASS]):
                    square.decalimg = 0
            else:
                square.decalimg = self.revindexes[self.IDX_GRASS][connflags]

        # And now return
        if (recurse):
            return affected
        else:
            return (curdecal != square.decalimg)
