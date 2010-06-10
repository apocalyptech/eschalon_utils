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

import random
from eschalon.map import Map

class ComplexObjStep(object):
    """
    A single step in a "complex" object.
    """
    def __init__(self, tile, dir=None, revdir=None):
        self.tile = tile
        self.dir = dir
        self.revdir = revdir

class ComplexObj(object):
    """
    An object to hold information about a "complex" object, meaning
    something which, in its atomic form, would take up more than one
    tile (examples being tents, beds, wagons, a carpet, and cliffs)
    """
    
    def __init__(self, name, starttile):
        self.name = name
        self.steps = [ComplexObjStep(starttile)]
        self.revdir = None
    def add(self, dir, tile):
        step = ComplexObjStep(tile)
        step.dir = dir
        self.steps[-1].revdir = self.revdir[dir]
        self.steps.append(step)
    def matches(self, matchtile):
        for step in self.steps:
            if step.tile == matchtile:
                return True
        return False
    def get_steps(self, tile):
        fwd = []
        rev = []
        for (i, step) in enumerate(self.steps):
            if step.tile == tile:
                for step in self.steps[i+1:]:
                    fwd.append((step.dir, step.tile))
                for step in reversed(self.steps[0:i]):
                    rev.append((step.revdir, step.tile))
                break
        return (fwd, rev)

class ComplexObjCollection(object):
    """
    Holds a bunch of ComplexObjs for you.
    """
    def __init__(self, revdir, var):
        self.objects = []
        self.revdir = revdir
        self.var = var
    def add(self, object):
        object.revdir = self.revdir
        self.objects.append(object)
    def get(self, id):
        for object in self.objects:
            if object.matches(id):
                return object
        return None

class SmartDraw(object):
    """
    A class to deal with "smart" drawing functions.

    An awful lot of this is really hacky and ugly.  Sorry about that.
    I pretty much didn't do any prior planning before coding any of
    this.
    """

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
    IDX_BIGFENCE = 4

    def __init__(self):

        # Construct some vars which'll be helpful later


        # Hardcoded Graphics info
        self.wallstarts = [161, 171, 181, 191, 201]
        self.fencestart = 73
        self.bigfencestart = 140
        self.special = 213
        self.tilesets = {
                self.IDX_GRASS: [9, 10, 11, 12],
                self.IDX_SAND: [124, 125]
            }
        self.random_terrain = [
                [3, 4],          # Red ground of some sort
                [9, 10, 11, 12], # Regular Grass
                [34, 35],        # Stone Ground
                [40, 41],        # Cobbles
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
        self.water = [ 126 ]

        # One empty dict for each IDX_*
        self.indexes = [ {}, {}, {}, {}, {} ]
        self.revindexes = [ {}, {}, {}, {}, {} ]
        self.beach_index = {}
        self.beach_revindex = {}

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

        # "Big" fence Indexes
        self.add_index(self.IDX_BIGFENCE, 0, self.DIR_NW|self.DIR_SE)
        self.add_index(self.IDX_BIGFENCE, 1, self.DIR_SW|self.DIR_NE)

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

        # Beach indexes (these are floor tiles, not decals - the directions
        # specified here are the direction that the SAND is in, not the
        # water.  Or to put it another way, these tiles are considered
        # water which happen to bleed into sand a bit.
        self.add_beach_index(124, self.DIR_NW|self.DIR_NE|self.DIR_SE|self.DIR_SW)
        self.add_beach_index(125, self.DIR_NW|self.DIR_NE|self.DIR_SE|self.DIR_SW)
        self.add_beach_index(127, self.DIR_NW)
        self.add_beach_index(128, self.DIR_SW)
        self.add_beach_index(129, self.DIR_E)
        self.add_beach_index(130, self.DIR_S)
        self.add_beach_index(131, self.DIR_NW|self.DIR_SW)
        self.add_beach_index(132, self.DIR_NW|self.DIR_NE)
        self.add_beach_index(133, self.DIR_SE)
        self.add_beach_index(134, self.DIR_NE)
        self.add_beach_index(135, self.DIR_W)
        self.add_beach_index(136, self.DIR_N)
        self.add_beach_index(137, self.DIR_NE|self.DIR_SE)
        self.add_beach_index(138, self.DIR_SW|self.DIR_SE)

        # Now smart Complex Objects
        self.complex_obj_floor = ComplexObjCollection(self.REV_DIR, 'floorimg')

        carpet = ComplexObj('Carpet', 73)
        self.complex_obj_floor.add(carpet)
        carpet.add(self.DIR_NE, 74)
        carpet.add(self.DIR_NE, 75)
        carpet.add(self.DIR_SE, 76)
        carpet.add(self.DIR_SW, 77)
        carpet.add(self.DIR_SW, 78)

        chasm_1 = ComplexObj('Chasm (1)', 85)
        self.complex_obj_floor.add(chasm_1)
        chasm_1.add(self.DIR_S, 91)
        chasm_1.add(self.DIR_S, 97)

        chasm_2 = ComplexObj('Chasm (2)', 86)
        self.complex_obj_floor.add(chasm_2)
        chasm_2.add(self.DIR_S, 92)
        chasm_2.add(self.DIR_S, 98)

        chasm_3 = ComplexObj('Chasm (3)', 87)
        self.complex_obj_floor.add(chasm_3)
        chasm_3.add(self.DIR_S, 93)
        chasm_3.add(self.DIR_S, 99)

        chasm_4 = ComplexObj('Chasm (4)', 88)
        self.complex_obj_floor.add(chasm_4)
        chasm_4.add(self.DIR_S, 94)
        chasm_4.add(self.DIR_S, 100)

        chasm_5 = ComplexObj('Chasm (5)', 89)
        self.complex_obj_floor.add(chasm_5)
        chasm_5.add(self.DIR_S, 95)
        chasm_5.add(self.DIR_S, 101)

        chasm_6 = ComplexObj('Chasm (6)', 90)
        self.complex_obj_floor.add(chasm_6)
        chasm_6.add(self.DIR_S, 96)
        chasm_6.add(self.DIR_S, 102)

        self.complex_obj_wall = ComplexObjCollection(self.REV_DIR, 'wallimg')
        
        bed_ne = ComplexObj('Bed (NE/SW)', 23)
        self.complex_obj_wall.add(bed_ne)
        bed_ne.add(self.DIR_NE, 24)

        bed_nw = ComplexObj('Bed (NW/SE)', 29)
        self.complex_obj_wall.add(bed_nw)
        bed_nw.add(self.DIR_SE, 30)

        tent_nw = ComplexObj('Tent (NW/SE)', 79)
        self.complex_obj_wall.add(tent_nw)
        tent_nw.add(self.DIR_E, 80)

        tent_ne = ComplexObj('Tent (NE/SW)', 81)
        self.complex_obj_wall.add(tent_ne)
        tent_ne.add(self.DIR_E, 82)

        wagon = ComplexObj('Wagon', 83)
        self.complex_obj_wall.add(wagon)
        wagon.add(self.DIR_NE, 84)

    def add_index(self, idxnum, index, connections):
        self.indexes[idxnum][index] = connections
        self.revindexes[idxnum][connections] = index

    def add_beach_index(self, index, connections):
        self.beach_index[index] = connections
        self.beach_revindex[connections] = index

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
        if (square.wallimg >= self.bigfencestart and square.wallimg < self.bigfencestart+2):
            return self.bigfencestart
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
        #if (wallgroup == self.fencestart):
        if (wallgroup in [self.fencestart, self.bigfencestart]):
            return self.draw_fence(square, wallgroup)
        #elif (wallgroup == self.bigfencestart):
        #    return self.draw_fence(square)

        # Now loop through our directions and see where we should link to.
        # We'll additionally call out to add_wall_connection() where appropriate
        # to update adjacent walls.
        connflags = 0
        flagcount = 0
        for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
            adjsquare = self.map.square_relative(square.x, square.y, testdir)
            if adjsquare is None:
                continue
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
            if testsquare is None:
                continue
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

    def draw_fence(self, square, fencestart):
        """
        Draws a fence.  If we've got here, we KNOW that we're a fence already.
        Note that there's a lot of duplicate code from draw_wall(), above, but
        there's enough differences that I'd rather not combine the two.

        Will return a list of squares that have been updated by this action
        (not including the given square, which is assumed).
        """

        retarr = []

        # Figure out what kind of fence we are
        if (fencestart == self.fencestart):
            idx = self.IDX_FENCE
        else:
            idx = self.IDX_BIGFENCE

        # Now loop through our directions and see where we should link to.
        # We'll additionally call out to add_fence_connection() where appropriate
        # to update adjacent walls.  We're hampered a bit since each fence square
        # can only support two connections.
        connflags = 0
        flagcount = 0
        for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
            adjsquare = self.map.square_relative(square.x, square.y, testdir)
            if adjsquare is None:
                continue
            adjgroup = self.get_wall_group(adjsquare)
            if (adjgroup is None or adjgroup != fencestart):
                continue
            connflags = connflags|testdir
            flagcount += 1
            if (fencestart == self.bigfencestart):
                # Our selection for the "big" fence is highly limited
                connflags = connflags|self.REV_DIR[testdir]
                flagcount += 1
                if (self.add_big_fence_connection(adjsquare, self.REV_DIR[testdir])):
                    retarr.append(adjsquare)
                break
            else:
                if (self.add_fence_connection(adjsquare, self.REV_DIR[testdir])):
                    retarr.append(adjsquare)
            if (flagcount == 2):
                break

        # Figure out what to put down if we don't actually have a match
        if (connflags not in self.revindexes[idx]):
            if (flagcount == 0):
                connflags = self.indexes[idx][0]
            elif (flagcount == 1):
                if ((connflags & self.DIR_NE) == self.DIR_NE or
                    (connflags & self.DIR_SW) == self.DIR_SW):
                    connflags = self.indexes[idx][0]
                else:
                    connflags = self.indexes[idx][1]
            else:
                raise Exception("flagcount isn't 1 or 0 - should figure out why")

        square.wallimg = fencestart + self.revindexes[idx][connflags]

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
            if testsquare is None:
                continue
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

    def add_big_fence_connection(self, square, dir):
        """
        Adds a connection to the "big" fence.  This is actually far simpler than
        add_fence_connection because we only have two possible "big" fence tiles,
        and since we know the direction, we already know which tile to use,
        basically.
        """
        connflags = dir
        connflags = connflags|self.REV_DIR[dir]
        newimg = self.bigfencestart + self.revindexes[self.IDX_BIGFENCE][connflags]
        if (newimg != square.wallimg):
            square.wallimg = newimg
            return True
        else:
            return False

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

        # Go elsewhere if we're drawing beach stuffs
        if (self.gui.get_widget('decalpref_beach').get_active()):
            return self.draw_beach(square)

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

    def draw_beach(self, square, recurse=True, known={}, parent_water=False):
        """
        Drawing beach tiles is handled differently from the usual decal
        stuff.  The overall flow is similar, but we're touching different
        vars, etc...
        """

        # TODO would be kind of nice to consider ANYTHING non-water to
        # be a sand "connection"

        # TODO: Gets touchy around the edge of the map

        connflags = 0
        connflags_not = 0
        flagcount = 0
        affected = []
        curdecal = square.decalimg
        curfloor = square.floorimg
        blacklist = []
        for idx in [self.IDX_GRASS, self.IDX_SAND]:
            blacklist.extend(self.indexes[self.IDX_GRASS].keys())

        # Find out if we're drawing a water tile, or one of the sand tiles
        drawing_water = False
        if (parent_water or (recurse and square.floorimg in self.water)):
            drawing_water = True

        # If recursing, load in all the squares we'll need, first
        # TODO: should just provide a function to get this, in Map
        if (recurse):
            for dir in [self.DIR_NE, self.DIR_E, self.DIR_SE, self.DIR_S,
                    self.DIR_SW, self.DIR_W, self.DIR_NW, self.DIR_N]:
                known[dir] = self.map.square_relative(square.x, square.y, dir)

            # Additionally, set our tile to full-sand so that the recursion
            # stuff can link in properly
            if square.floorimg in self.beach_index.keys():
                square.floorimg = self.tilesets[self.IDX_SAND][0]

            # We're going to recurse now rather than later
            for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW,
                self.DIR_N, self.DIR_E, self.DIR_S, self.DIR_W]:
                adjsquare = self.get_rel(square, known, testdir)
                if (adjsquare):
                    if (self.draw_beach(adjsquare, False, { self.REV_DIR[testdir]: square }, drawing_water)):
                        affected.append(adjsquare)

        # First find out more-typical adjacent squares
        if (square.floorimg in self.beach_index.keys() + self.water):

            # Let's put down a full-sand tile in place of whatever we actually put in,
            # under the assumption that the tile we're drawing should be mostly sand.
            if recurse and square.floorimg not in self.water:
                square.floorimg = self.tilesets[self.IDX_SAND][0]

            for testdir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
                adjsquare = self.get_rel(square, known, testdir)
                if (not adjsquare):
                    continue
                # Two criteria for accepting a connection for the given direction:
                #    1) The adjacent square is one of our defined "beach" tiles AND the tile
                #       has sand facing in our direction
                #  -or-
                #    2) The adjacent square is NOT one of our "beach" tiles but is also not water.
                # We do this because we'd like to consider anything non-sand to be virtually "sand"
                if ((adjsquare.floorimg in self.beach_index.keys() and
                    (self.beach_index[adjsquare.floorimg] & self.REV_DIR[testdir]) == self.REV_DIR[testdir])
                    or (adjsquare.floorimg not in self.beach_index.keys() and adjsquare.floorimg not in self.water)):
                    connflags = connflags|testdir
                    flagcount += 1
                else:
                    connflags_not = connflags_not|testdir

            # There's two blocks of code here with varying conditions for running.
            # I think it might be a little less cumbersome to trigger them this way.
            process_four = False
            process_special = False
            if drawing_water:
                if (flagcount in [4, 3]):
                    process_four = True
                elif (connflags != 0 and connflags not in self.beach_revindex):
                    process_special = True
            else:
                if (flagcount == 4 or (connflags != 0 and connflags not in self.beach_revindex)):
                    process_four = True

            # Now we're ready to see if we have anything closer which might match
            if process_four:
                # We're completely surrounded by water.  Unless we're drawing a water
                # tile and happen to be processing the "center" tile still, convert us
                # to a full-sand piece.
                if (not recurse or square.floorimg not in self.water):
                    square.floorimg = self.tilesets[self.IDX_SAND][0]
            elif process_special:
                # The only case of being in here would be if we're drawing water, and we
                # have two connections which happen to be adjacent from each other.  For
                # now, just pick one to delete at random.  When we're drawing sand, I prefer
                # the more "chunky" drawing which results from the process_four block
                #
                # TODO: it would be nice to check the relevant cardinal directions to see if
                # there's one that matches better than the other.
                for dir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
                    if ((connflags & dir) == dir):
                        connflags = connflags & ~dir
                        square.floorimg = self.beach_revindex[connflags]
                        break
            else:
                # See if there's a more-specific tile we could match on
                for testdir in [self.DIR_N, self.DIR_E, self.DIR_S, self.DIR_W]:
                    if ((connflags|testdir) in self.beach_revindex):
                        adjsquare = self.get_rel(square, known, testdir)
                        if (not adjsquare):
                            continue
                        # To add in this direction as a "connection", this compound statement has to be true:
                        #   1) The adjacent square is in our collection of beach tiles
                        # -AND-
                        #     a) The adjacent square has sand pointing in our direction
                        #    -or-
                        #     b) The adjacent square is "virtually" pointing in our direction (via ADJ_DIR)
                        # -AND-
                        #   2) We must have a tile which matches the resulting connection, of course.
                        # TODO: Seems ugly, would like to simplify.  Also, like above, we should probably
                        # consider any non-"beach" tile to be a connection, yes?
                        if (adjsquare.floorimg in self.beach_index.keys() and
                            ((self.beach_index[adjsquare.floorimg] & self.REV_DIR[testdir]) == self.REV_DIR[testdir] or
                             (self.beach_index[adjsquare.floorimg] & self.ADJ_DIR[self.REV_DIR[testdir]]) == self.ADJ_DIR[self.REV_DIR[testdir]])):
                            if ((connflags | testdir) in self.beach_revindex):
                                connflags = connflags | testdir
                                if (flagcount != 0):
                                    break
                if (connflags == 0):
                    # If we're here, there's no sand surrounding us at all.
                    # Set ourselves to water.
                    square.floorimg = self.water[0]
                else:
                    square.floorimg = self.beach_revindex[connflags]

        # Check our decal blacklist, after all that, and filter it out if there's
        # something here which shouldn't be.
        if square.decalimg in blacklist:
            square.decalimg = 0

        # And now return
        if (recurse):
            return affected
        else:
            return (curdecal != square.decalimg or curfloor != square.floorimg)

    def draw_smart_complex_obj(self, collection, square, undo):
        """
        Sees if we can draw a complex wall object.
        """
        affected = []
        text = None
        obj = collection.get(square.__dict__[collection.var])
        if obj is not None:
            text = obj.name
            (fwd, rev) = obj.get_steps(square.__dict__[collection.var])
            for series in (fwd, rev):
                (curx, cury) = (square.x, square.y)
                for (dir, id) in series:
                    newsquare = self.map.square_relative(curx, cury, dir)
                    if newsquare:
                        if (newsquare.__dict__[collection.var] != id):
                            undo.add_additional(newsquare)
                            affected.append(newsquare)
                            newsquare.__dict__[collection.var] = id
                            (curx, cury) = (newsquare.x, newsquare.y)
                    else:
                        break
        return (text, affected)

    def draw_smart_complex_wall(self, square, undo):
        return self.draw_smart_complex_obj(self.complex_obj_wall, square, undo)

    def draw_smart_complex_floor(self, square, undo):
        return self.draw_smart_complex_obj(self.complex_obj_floor, square, undo)

