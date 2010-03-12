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

    DIR_N = Map.DIR_N
    DIR_NE = Map.DIR_NE
    DIR_E = Map.DIR_E
    DIR_SE = Map.DIR_SE
    DIR_S = Map.DIR_S
    DIR_SW = Map.DIR_SW
    DIR_W = Map.DIR_W
    DIR_NW = Map.DIR_NW

    REV_DIR = {
            DIR_NE: DIR_SW,
            DIR_SE: DIR_NW,
            DIR_SW: DIR_NE,
            DIR_NW: DIR_SE,
            DIR_N: DIR_S,
            DIR_E: DIR_W,
            DIR_S: DIR_N,
            DIR_W: DIR_E
        }

    ADJ_DIR = {
            DIR_NE: DIR_N|DIR_E,
            DIR_SE: DIR_S|DIR_E,
            DIR_SW: DIR_S|DIR_W,
            DIR_NW: DIR_N|DIR_W,
            DIR_N: DIR_NE|DIR_NW,
            DIR_E: DIR_NE|DIR_SE,
            DIR_S: DIR_SE|DIR_SW,
            DIR_W: DIR_NW|DIR_SW
        }

    # List of adjacent directions if we're just
    # looking at cardinal directions
    CARD_ADJ_DIRS ={
            DIR_N: [DIR_W, DIR_E],
            DIR_S: [DIR_W, DIR_E],
            DIR_W: [DIR_N, DIR_S],
            DIR_E: [DIR_N, DIR_S]
        }

    COMP_DIR = {
            DIR_N|DIR_W: DIR_NW,
            DIR_N|DIR_E: DIR_NE,
            DIR_S|DIR_E: DIR_SE,
            DIR_S|DIR_W: DIR_SW
        }

    IDX_WALL = 0
    IDX_FENCE = 1
    IDX_GRASS = 2
    IDX_SAND = 3

    def __init__(self):

        # Construct some vars which'll be helpful later


        # Hardcoded Graphics info
        self.wallstarts = [161, 171, 181, 191, 201]
        self.fencestart = 73
        self.special = 213
        self.tilesets = {
                self.IDX_GRASS: [9, 10, 11, 12],
                self.IDX_SAND: [124, 125]
            }
        self.random_terrain = [
                [9, 10, 11, 12], # Regular Grass
                [79, 80, 81, 82] # "Dry" Grass
            ]
        self.random_obj = [
                [91, 92, 93],         # Shrubs
                [95, 96],             # Marshy Shrubs
                [127, 128],           # Blossoming Trees
                [129, 130, 131, 142], # Whithered Trees
                [219, 220],           # Tall Rocks
                [251, 252],           # Tall Trees
                [253, 254]            # Tall Pines
            ]
        self.random_walldecal = [
                [9, 10],    # Wall shadows/smudges (SW->NE)
                [11, 12],   # Wall shadows/smudges (NW->SE)
                [27, 28],   # Cracks (NW->SE)
                [29, 30]    # Cracks (SW->NE)
            ]

        # One empty dict for each IDX_*
        self.indexes = [ {}, {}, {}, {} ]
        self.revindexes = [ {}, {}, {}, {} ]

        # Other vars we'll need to keep track of
        self.map = None
        self.gui = None

        # Wall Indexes
        self.add_index(self.IDX_WALL, -1, self.DIR_NE|self.DIR_SE|self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_WALL, 0, self.DIR_NE|self.DIR_SW)
        self.add_index(self.IDX_WALL, 1, self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_WALL, 2, self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_WALL, 3, self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_WALL, 4, self.DIR_NE|self.DIR_NW)
        self.add_index(self.IDX_WALL, 5, self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_WALL, 6, self.DIR_SE|self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_WALL, 7, self.DIR_NE|self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_WALL, 8, self.DIR_NE|self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_WALL, 9, self.DIR_NE|self.DIR_SE|self.DIR_SW)

        # Fence Indexes
        self.add_index(self.IDX_FENCE, 0, self.DIR_NE|self.DIR_SW)
        self.add_index(self.IDX_FENCE, 1, self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_FENCE, 2, self.DIR_SW|self.DIR_SE)
        self.add_index(self.IDX_FENCE, 3, self.DIR_NW|self.DIR_SW)
        self.add_index(self.IDX_FENCE, 4, self.DIR_NE|self.DIR_NW)
        self.add_index(self.IDX_FENCE, 5, self.DIR_SE|self.DIR_NE)

        # Grass Indexes
        self.add_index(self.IDX_GRASS, 97, self.DIR_SE)
        self.add_index(self.IDX_GRASS, 98, self.DIR_SW)
        self.add_index(self.IDX_GRASS, 99, self.DIR_NW)
        self.add_index(self.IDX_GRASS, 100, self.DIR_NE)
        self.add_index(self.IDX_GRASS, 101, self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 102, self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 103, self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 104, self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 105, self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 106, self.DIR_NE|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 107, self.DIR_N)
        self.add_index(self.IDX_GRASS, 108, self.DIR_S)
        self.add_index(self.IDX_GRASS, 109, self.DIR_W)
        self.add_index(self.IDX_GRASS, 110, self.DIR_E)
        self.add_index(self.IDX_GRASS, 126, self.DIR_N|self.DIR_S)
        self.add_index(self.IDX_GRASS, 143, self.DIR_W|self.DIR_E)
        self.add_index(self.IDX_GRASS, 157, self.DIR_W|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 158, self.DIR_N|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 159, self.DIR_E|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 160, self.DIR_W|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 161, self.DIR_E|self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 162, self.DIR_W|self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 163, self.DIR_N|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 164, self.DIR_E|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 165, self.DIR_S|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 166, self.DIR_S|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 167, self.DIR_N|self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 168, self.DIR_S|self.DIR_NW|self.DIR_NE)

        # Sand Indexes
        self.add_index(self.IDX_SAND, 138, self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_SAND, 144, self.DIR_NE|self.DIR_SW)
        self.add_index(self.IDX_SAND, 145, self.DIR_NW)
        self.add_index(self.IDX_SAND, 146, self.DIR_NE)
        self.add_index(self.IDX_SAND, 147, self.DIR_SE)
        self.add_index(self.IDX_SAND, 148, self.DIR_SW)
        self.add_index(self.IDX_SAND, 149, self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_SAND, 150, self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_SAND, 155, self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_SAND, 156, self.DIR_NW|self.DIR_NE)

        # Pool to randomly choose from if we're completely surrounded
        self.tile_fullest = {
                self.IDX_GRASS: [161, 162, 167, 168],
                self.IDX_SAND: [138, 144]
            }

    def add_index(self, idxnum, index, connections):
        self.indexes[idxnum][index] = connections
        self.revindexes[idxnum][connections] = index

    def set_map(self, map):
        self.map = map

    def set_gui(self, gui):
        self.gui = gui

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
            # If we're not drawing a wall, see if we should be randomizing
            # anything
            if (self.gui.smart_randomize.get_active()):
                for tileset in self.random_obj:
                    if square.wallimg in tileset:
                        square.wallimg = random.choice(tileset)
                        break
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
        for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
            adjsquare = self.map.square_relative(square.x, square.y, testdir)
            adjgroup = self.get_wall_group(adjsquare, wallgroup)
            if (adjgroup is None or adjgroup != wallgroup):
                continue
            connflags = connflags|testdir
            flagcount += 1
            if (self.add_wall_connection(wallgroup, adjsquare, self.REV_DIR[testdir])):
                retarr.append(adjsquare)

        # Figure out what to put down if we don't actually have a match
        if (connflags not in self.revindexes[self.IDX_WALL]):
            if (flagcount == 0):
                connflags = self.indexes[self.IDX_WALL][0]
            elif (flagcount == 1):
                if ((connflags & self.DIR_NE) == self.DIR_NE or
                    (connflags & self.DIR_SW) == self.DIR_SW):
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
        for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
            if (testdir == dir):
                continue
            testsquare = self.map.square_relative(square.x, square.y, testdir)
            testgroup = self.get_wall_group(testsquare, group)
            if (testgroup and testgroup == group):
                conncount += 1
                newflags = (newflags | testdir)

        # Now clean up.  If there were no connections found, just use the
        # appropriate straight tile.  If 1, just add in our connection.
        # Otherwise, accept the pruning.
        if (conncount == 0):
            if (dir == self.DIR_NE or dir == self.DIR_SW):
                newflags = self.DIR_NE|self.DIR_SW
            else:
                newflags = self.DIR_NW|self.DIR_SE

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
        for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
            adjsquare = self.map.square_relative(square.x, square.y, testdir)
            adjgroup = self.get_wall_group(adjsquare)
            if (adjgroup is None or adjgroup != self.fencestart):
                continue
            connflags = connflags|testdir
            flagcount += 1
            if (self.add_fence_connection(adjsquare, self.REV_DIR[testdir])):
                retarr.append(adjsquare)
            if (flagcount == 2):
                break

        # Figure out what to put down if we don't actually have a match
        if (connflags not in self.revindexes[self.IDX_FENCE]):
            if (flagcount == 0):
                connflags = self.indexes[self.IDX_FENCE][0]
            elif (flagcount == 1):
                if ((connflags & self.DIR_NE) == self.DIR_NE or
                    (connflags & self.DIR_SW) == self.DIR_SW):
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
        for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
            if (testdir == dir):
                continue
            testsquare = self.map.square_relative(square.x, square.y, testdir)
            testgroup = self.get_wall_group(testsquare)
            if (testgroup and testgroup == self.fencestart):
                conncount += 1
                newflags = (newflags | testdir)
                break

        # Now clean up.  If there were no connections found, just use the
        # appropriate straight tile.  If 1, just add in our connection.
        # Otherwise, accept the pruning.
        if (conncount == 0):
            if (dir == self.DIR_NE or dir == self.DIR_SW):
                newflags = self.DIR_NE|self.DIR_SW
            else:
                newflags = self.DIR_NW|self.DIR_SE

        # Now after all that, see if we even changed at all.  If so,
        # make the change and report back.
        if (curflags == newflags):
            return False
        else:
            square.wallimg = self.fencestart + self.revindexes[self.IDX_FENCE][newflags]
            return True

    def get_rel(self, square, known, dir):
        """
        Given a square, a "known" array, and a direction, return the square in
        that direction.  This will update "known" appropriately when a square
        isn't found.
        """
        if (dir not in known):
            known[dir] = self.map.square_relative(square.x, square.y, dir)
        return known[dir]

    def draw_floor(self, square, straight_path=True, recurse=True, known={}):
        """
        Given a square, figure out what kind of grass decals it should have,
        if any.  Will actually set the decal image, as well.  If 'recurse'
        is True, we'll make recursive calls to do the same with adjacent
        squares.  Using 'known' you can pass in any squares which may have
        already been loaded (which can help avoid unnecessary calls to
        Map.square_relative().
        
        Returns a list of modified squares if we're recursing, or just
        true/false otherwise.  (Note that the list does not include the
        original square, which is just assumed.)

        It should be noted that I stumbled across the "straight_path" stuff
        purely by accident; that wasn't actually my goal when I first
        started out.  Most of Eschalon uses what these functions would call
        non-straight paths.
        """

        # TODO: We probably only want to overwrite decals that we would
        # have put in place; not other decals
        # TODO: Single squares of water in the middle of other terrain
        # should be not a wall

        connflags = 0
        connflags_not = 0
        flagcount = 0
        affected = []
        curdecal = square.decalimg
        curfloor = square.floorimg

        # If recursing, load in all the squares we'll need, first
        # TODO: should just provide a function to get this, in Map
        if (recurse):
            for dir in [self.DIR_NE, self.DIR_E, self.DIR_SE, self.DIR_S,
                    self.DIR_SW, self.DIR_W, self.DIR_NW, self.DIR_N]:
                known[dir] = self.map.square_relative(square.x, square.y, dir)

            # Also randomize the floor tile if we're supposed to (we only do
            # this to the tile actually being drawn, not any adjacent tiles)
            if (self.gui.smart_randomize.get_active()):
                for tileset in self.random_terrain:
                    if curfloor in tileset:
                        square.floorimg = random.choice(tileset)
                        break

        # Figure out whether to try and fit grass decals or sand decals,
        # and which decal type to strip out
        if (self.gui.get_widget('decalpref_grass').get_active()):
            idxtype = self.IDX_GRASS
            blacklist = [self.IDX_SAND]
        elif (self.gui.get_widget('decalpref_sand').get_active()):
            idxtype = self.IDX_SAND
            blacklist = [self.IDX_GRASS]
        else:
            # TODO: We should probably raise an exception or something here,
            # instead...
            return

        # First find out more-typical adjacent squares
        for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
            adjsquare = self.get_rel(square, known, testdir)
            if (not adjsquare):
                continue
            if (adjsquare.floorimg in self.tilesets[idxtype]):
                connflags = connflags|testdir
                flagcount += 1
            else:
                connflags_not = connflags_not|testdir

            # Process adjacent squares if we're supposed to
            if (recurse):
                # TODO: commented this out when I switched over to controlling idxtype
                # via the GUI; leaving it here for now in case I notice weird behavior.
                # Anyway, take this note out once it's been in-place for awhile.  Ditto
                # for the block below...
                #if (adjsquare.floorimg not in self.tilesets[idxtype]):
                if (self.draw_floor(adjsquare, straight_path, False, { self.REV_DIR[testdir]: square })):
                    affected.append(adjsquare)

        # If we're recursing, we'll need to check the cardinal directions as
        # well, to clear out errant corner-connection decals
        # TODO: We should really just grab all these at the beginning and
        # cache them.
        if (recurse):
            for testdir in [self.DIR_N, self.DIR_E, self.DIR_S, self.DIR_W]:
                adjsquare = self.get_rel(square, known, testdir)
                if (not adjsquare):
                    continue
                #if (adjsquare.floorimg not in self.tilesets[idxtype]):
                if (self.draw_floor(adjsquare, straight_path, False, { self.REV_DIR[testdir]: square })):
                    affected.append(adjsquare)

        if (square.floorimg in self.tilesets[idxtype]):

            # Now let's just get out of here if we're a grass square ourselves.
            # We could have exited earlier, but this way we can recurse around ourselves
            # without duplicating much code.
            for idx in [self.IDX_GRASS, self.IDX_SAND]:
                if (square.decalimg in self.indexes[idx].keys()):
                    square.decalimg = 0

        else:

            # Now refine the list
            if (flagcount > 2):

                # If we're this full, just pull from our "fullest" list
                # instead
                if (flagcount == 4):
                    # Just pick a random one from our "fullest" pool
                    square.decalimg = random.choice(self.tile_fullest[idxtype])
                elif (flagcount == 3):
                    # Pick one from the "fullest" pool which matches
                    # most closely
                    for choice in self.tile_fullest[idxtype]:
                        choiceflags = self.indexes[idxtype][choice]
                        if ((choiceflags & connflags_not) == 0):
                            square.decalimg = choice
                            break

                # Prune, in case there are adjacent tiles
                curflags = self.indexes[idxtype][square.decalimg]
                for testdir in [self.DIR_N, self.DIR_E, self.DIR_S, self.DIR_W]:
                    adjsquare = self.get_rel(square, known, testdir)
                    if (not adjsquare):
                        continue
                    if (adjsquare.floorimg not in self.tilesets[idxtype]):
                        curflags = (curflags & ~testdir)
                if (curflags in self.revindexes[idxtype]):
                    square.decalimg = self.revindexes[idxtype][curflags]
            else:
                # See if there's a more-specific tile we could match on
                for testdir in [self.DIR_N, self.DIR_E, self.DIR_S, self.DIR_W]:
                    if (connflags & self.ADJ_DIR[testdir] == 0):
                        if (straight_path):
                            found_adj_same = False
                            for adjdir in self.CARD_ADJ_DIRS[testdir]:
                                adjsquare = self.get_rel(square, known, self.COMP_DIR[testdir|adjdir])
                                if (not adjsquare):
                                    continue
                                if (adjsquare.floorimg in self.tilesets[idxtype]):
                                    # TODO: should check for non-grass decals here (sand, etc)
                                    found_adj_same = True
                                    break
                                elif (adjsquare.decalimg in self.indexes[idxtype]):
                                    adjflags = self.indexes[idxtype][adjsquare.decalimg]
                                    testflag = self.COMP_DIR[self.REV_DIR[adjdir]|testdir]
                                    if (adjflags == testflag):
                                        found_adj_same = True
                                        break
                            if (not found_adj_same):
                                continue
                    if ((connflags|testdir) in self.revindexes[idxtype]):
                        adjsquare = self.get_rel(square, known, testdir)
                        if (not adjsquare):
                            continue
                        if (adjsquare.floorimg in self.tilesets[idxtype]):
                            connflags = connflags | testdir
                            if (flagcount != 0):
                                break
                if (connflags == 0):
                    for idx in [self.IDX_GRASS, self.IDX_SAND]:
                        if (square.decalimg in self.indexes[idx]):
                            square.decalimg = 0
                else:
                    square.decalimg = self.revindexes[idxtype][connflags]

        # Check our blacklist, after all that, and filter it out if we've been bad
        for item in blacklist:
            if square.decalimg in self.indexes[item].keys():
                square.decalimg = 0
                break

        # And now return
        if (recurse):
            return affected
        else:
            return (curdecal != square.decalimg or curfloor != square.floorimg)

    def draw_walldecal(self, square):
        """
        Draws using the given wall decal.  Right now this just processes randomization
        if we're asked to
        """
        # First set up and make sure that we're even drawing a wall
        retarr = []
        if (self.gui.smart_randomize.get_active()):
            for tileset in self.random_walldecal:
                if square.walldecalimg in tileset:
                    square.walldecalimg = random.choice(tileset)
                    break
        return None
