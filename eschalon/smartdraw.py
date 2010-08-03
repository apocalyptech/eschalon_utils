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

import random
from eschalon import constants as c
from eschalon.map import Map
from eschalon.square import Square
from eschalon.mapscript import Mapscript

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
    
    def __init__(self, name, starttile, wallflag=None):
        self.name = name
        self.steps = [ComplexObjStep(starttile)]
        self.revdir = None
        self.wallflag = wallflag
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

class PremadeObject(object):
    """
    A class to hold information about a premade object.  For instance,
    it'd be nice to be able to just plop a door down, or a chest,
    without having to do the actual object creation in the square
    editor.
    """

    # TODO: combine Premade and Complex, eh?  Doors should have the
    # frame adjacent, etc.
    def __init__(self, name):
        self.name = name
        self.square = Square.new(c.book, -1, -1)
        self.square.savegame = True
        self.mapscript = None
        self.do_wall = False
        self.do_floorimg = False
        self.do_decalimg = False
        self.do_wallimg = False
        self.do_walldecalimg = False
        self.do_script = False

    def set_wall(self, wall):
        self.do_wall = True
        self.square.wall = wall

    def set_floorimg(self, floorimg):
        self.do_floorimg = True
        self.square.floorimg = floorimg

    def set_decalimg(self, decalimg):
        self.do_decalimg = True
        self.square.decalimg = decalimg

    def set_wallimg(self, wallimg):
        self.do_wallimg = True
        self.square.wallimg = wallimg

    def set_walldecalimg(self, floorimg):
        self.do_walldecalimg = True
        self.square.walldecalimg = floorimg

    def set_script(self, scriptid):
        self.do_script = True
        self.square.scriptid = scriptid

    def create_scriptobj(self, initcontents='random'):
        self.mapscript = Mapscript.new(c.book, True)
        self.mapscript.tozero(-1, -1)
        if initcontents is not None:
            self.mapscript.items[0].item_name = initcontents

    def apply_to(self, map, square):
        if self.do_wall:
            square.wall = self.square.wall
        if self.do_floorimg:
            square.floorimg = self.square.floorimg
        if self.do_decalimg:
            square.decalimg = self.square.decalimg
        if self.do_wallimg:
            square.wallimg = self.square.wallimg
        if self.do_walldecalimg:
            square.walldecalimg = self.square.walldecalimg
        if self.do_script:
            square.scriptid = self.square.scriptid
            for i in range(len(square.scripts)):
                map.delscript(square.x, square.y, 0)
            if self.mapscript is not None:
                square.addscript(self.mapscript.replicate())
                map.scripts.append(square.scripts[0])
                square.scripts[0].x = square.x
                square.scripts[0].y = square.y

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

    # Note that Beach is a special one, but we put it in the list
    # so that our newer-style decalpref dropdown has a value to use
    IDX_WALL = 0
    IDX_FENCE = 1
    IDX_GRASS = 2
    IDX_SAND = 3
    IDX_BIGFENCE = 4
    IDX_SNOW = 5
    IDX_LAVA = 6
    IDX_BEACH = 7

    def __init__(self):

        # One empty dict for each IDX_*
        self.indexes = [ {}, {}, {}, {}, {}, {}, {}, {} ]
        self.revindexes = [ {}, {}, {}, {}, {}, {}, {}, {} ]
        self.beach_index = {}
        self.beach_revindex = {}

        # Other vars we'll need to keep track of
        self.map = None
        self.gui = None

        # Now populate all the actual constants
        self.init_vars()

    def init_vars(self):
        """
        This is where the implementing class will define all of the actually-important
        data that SmartDraw needs.
        """
        pass

    def add_index(self, idxnum, index, connections):
        self.indexes[idxnum][index] = connections
        self.revindexes[idxnum][connections] = index

    def add_beach_index(self, index, connections):
        self.beach_index[index] = connections
        self.beach_revindex[connections] = index

    def set_map(self, map):
        self.map = map
        for obj in self.premade_objects:
            obj.square.savegame = map.is_savegame()
            if obj.mapscript is not None:
                obj.mapscript.savegame = map.is_savegame()

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
        if (square.wallimg in self.fenceids):
            return self.fenceids[0]
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
        if (wallgroup in [self.fenceids[0], self.bigfencestart]):
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
        if (fencestart == self.fenceids[0]):
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
                # In both B1 and B2, our first two fence images are the straight ones
                for fenceidx in [0, 1]:
                    for dir in [self.DIR_NE, self.DIR_SW, self.DIR_SE, self.DIR_NW]:
                        if ((connflags & dir) == dir and (self.indexes[idx][fenceidx] & dir) == dir):
                            connflags = self.indexes[idx][fenceidx]
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
        idx = square.wallimg - self.fenceids[0]
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
            if (testgroup and testgroup == self.fenceids[0]):
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
            square.wallimg = self.fenceids[0] + self.revindexes[self.IDX_FENCE][newflags]
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
        iter = self.gui.get_widget('decalpref').get_active_iter()
        model = self.gui.get_widget('decalpref').get_model()
        idxtype = model.get_value(iter, 1)
        if (idxtype == self.IDX_BEACH):
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
        decalpref_blacklists = {}
        full_idx_list = [self.IDX_GRASS, self.IDX_SAND, self.IDX_SNOW, self.IDX_LAVA]
        for idx in full_idx_list:
            decalpref_blacklists[idx] = []
            for inner_idx in full_idx_list:
                if idx != inner_idx:
                    decalpref_blacklists[idx].append(inner_idx)
        if idxtype in decalpref_blacklists:
            blacklist = decalpref_blacklists[idxtype]
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
            for idx in full_idx_list:
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
                    for idx in full_idx_list:
                        if (square.decalimg in self.indexes[idx]):
                            square.decalimg = 0
                else:
                    square.decalimg = self.revindexes[idxtype][connflags]

        # Check our blacklist, after all that, and filter it out if we've been bad
        for item in blacklist:
            if square.decalimg in self.indexes[item].keys():
                square.decalimg = 0
                break

        # Finally, if we're handling Lava tiles, we need to do one more recursive loop
        # to draw a complimentary decal on the actual Lava tiles themselves.
        if (recurse and idxtype == self.IDX_LAVA):
            newaffected = self.draw_complimentary_decals(idxtype, square, known)
            for testsquare in newaffected:
                if testsquare not in affected:
                    affected.append(testsquare)

        # And now return
        if (recurse):
            return affected
        else:
            return (curdecal != square.decalimg or curfloor != square.floorimg)

    def draw_complimentary_decals(self, idxtype, centersquare, known):
        """
        This is an extra recursive loop, run after the main draw_floor() routine,
        which will "double up" decal images (eg: for Book 2 Lava decals, which
        needs to have a decal on the lava tiles themselves).  Note that, unfortunately,
        to process this correctly, we have to recurse an additional level out.
        """
        actionsquares = []
        for square in [centersquare] + known.values():
            if square is None:
                continue
            if square.floorimg not in self.tilesets[idxtype]:
                continue
            connflags = 0
            flagcount = 0
            for dir in [self.DIR_NE, self.DIR_SE, self.DIR_SW, self.DIR_NW]:
                adjsquare = self.map.square_relative(square.x, square.y, dir)
                if adjsquare is None:
                    continue
                if adjsquare.floorimg in self.tilesets[idxtype]:
                    continue
                if adjsquare.decalimg in self.indexes[idxtype]:
                    idxdir = self.indexes[idxtype][adjsquare.decalimg]
                    if (idxdir & self.REV_DIR[dir] == self.REV_DIR[dir]):
                        flagcount += 1
                        connflags = connflags | dir
            if flagcount == 4:
                actionsquares.append((square, random.choice(self.tile_fullest[idxtype])))
            elif flagcount == 0:
                actionsquares.append((square, 0))
            else:
                actionsquares.append((square, self.revindexes[idxtype][connflags]))
        affected = []
        for (square, newdecal) in actionsquares:
            if square.decalimg != newdecal:
                affected.append(square)
                square.decalimg = newdecal
        return affected

    def draw_decal(self, square):
        """
        Draws using the given decal.  Right now this just processes randomization
        if we're asked to
        """
        # First set up and make sure that we're even drawing a wall
        retarr = []
        if (self.gui.smart_randomize.get_active()):
            for tileset in self.random_decal:
                if square.decalimg in tileset:
                    square.decalimg = random.choice(tileset)
                    break
        return None

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
        for idx in [self.IDX_GRASS, self.IDX_SAND, self.IDX_SNOW, self.IDX_LAVA]:
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
                            if obj.wallflag is not None:
                                newsquare.wall = obj.wallflag
                    else:
                        break
        return (text, affected)

    def draw_smart_complex_wall(self, square, undo):
        return self.draw_smart_complex_obj(self.complex_obj_wall, square, undo)

    def draw_smart_complex_floor(self, square, undo):
        return self.draw_smart_complex_obj(self.complex_obj_floor, square, undo)

    def draw_smart_complex_decal(self, square, undo):
        return self.draw_smart_complex_obj(self.complex_obj_decal, square, undo)

    def place_object(self, square, objidx):
        """
        Places a premade object on a square
        """
        self.premade_objects[objidx].apply_to(self.map, square)

    @staticmethod
    def new(book):
        """
        Static method to initialize the correct object
        """
        if book == 1:
            return B1SmartDraw()
        else:
            return B2SmartDraw()

class B1SmartDraw(SmartDraw):
    """
    SmartDraw for Book 1
    """

    book = 1

    def init_vars(self):

        # Various lists to keep track of which objects should be walls
        self.wall_list = {}
        self.wall_list['floor_seethrough'] = range(83, 103) + [126]
        self.wall_list['decal_blocked'] = [55]
        self.wall_list['decal_seethrough'] = [52, 71, 83, 84, 96, 170]
        self.wall_list['wall_blocked'] = (range(23, 31) + range(68, 72) + range(80, 85) +
            range(109, 112) + range(116, 121) + range(125, 144) +
            range(145, 156) + range(161, 214) + range(251, 256) + 
            [38, 40, 43, 49, 50, 58, 59, 79, 89, 101, 103, 105, 107, 215, 216, 219, 220])
        self.wall_list['wall_seethrough'] = (range(1, 23) + range(31, 38) + range(44, 49) +
            range(51, 56) + range(60, 68) + range(72, 79) +
            range(85, 89) + range(112, 116) + range(121, 125) +
            [39, 41, 42, 57, 144, 214])
        self.wall_list['walldecal_seethrough'] = [19, 20]
        self.wall_list['wall_restrict'] = []

        # Hardcoded Graphics info
        self.wallstarts = [161, 171, 181, 191, 201]
        self.fenceids = range(73, 79)
        self.bigfencestart = 140
        self.special = 213
        self.tilesets = {
                self.IDX_GRASS: [9, 10, 11, 12],
                self.IDX_SAND: [124, 125],
                self.IDX_SNOW: [],
                self.IDX_LAVA: [],
            }
        self.random_terrain = [
                [3, 4],          # Red ground of some sort
                [9, 10, 11, 12], # Regular Grass
                [34, 35],        # Stone Ground
                [40, 41],        # Cobbles
                [79, 80, 81, 82] # "Dry" Grass
            ]
        self.random_decal = [
                range(13, 19),    # Bloodstains, small-to-med
                range(26, 31),    # Brown smudges
                [31, 32],         # Hay/Straw
                [37, 43, 49],     # Smudges
                [50, 51, 56, 57], # Dead bodies
                [73, 74, 82],     # Scattered wood
                [75, 76],         # Rubble
                [77, 78],         # Smashed somethingorother
                [79, 80],         # Skeletons
                [88, 89, 90],     # Mushrooms
                [116, 117, 118, 119], # Cracks
                [44, 169],        # Greenish smudge
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
                self.IDX_SAND: [138, 144],
                self.IDX_SNOW: [],
                self.IDX_LAVA: [],
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

        chasm_1 = ComplexObj('Chasm (1)', 85, 5)
        self.complex_obj_floor.add(chasm_1)
        chasm_1.add(self.DIR_S, 91)
        chasm_1.add(self.DIR_S, 97)

        chasm_2 = ComplexObj('Chasm (2)', 86, 5)
        self.complex_obj_floor.add(chasm_2)
        chasm_2.add(self.DIR_S, 92)
        chasm_2.add(self.DIR_S, 98)

        chasm_3 = ComplexObj('Chasm (3)', 87, 5)
        self.complex_obj_floor.add(chasm_3)
        chasm_3.add(self.DIR_S, 93)
        chasm_3.add(self.DIR_S, 99)

        chasm_4 = ComplexObj('Chasm (4)', 88, 5)
        self.complex_obj_floor.add(chasm_4)
        chasm_4.add(self.DIR_S, 94)
        chasm_4.add(self.DIR_S, 100)

        chasm_5 = ComplexObj('Chasm (5)', 89, 5)
        self.complex_obj_floor.add(chasm_5)
        chasm_5.add(self.DIR_S, 95)
        chasm_5.add(self.DIR_S, 101)

        chasm_6 = ComplexObj('Chasm (6)', 90, 5)
        self.complex_obj_floor.add(chasm_6)
        chasm_6.add(self.DIR_S, 96)
        chasm_6.add(self.DIR_S, 102)

        self.complex_obj_wall = ComplexObjCollection(self.REV_DIR, 'wallimg')
        
        bed_ne = ComplexObj('Bed (NE/SW)', 23, 1)
        self.complex_obj_wall.add(bed_ne)
        bed_ne.add(self.DIR_NE, 24)

        bed_nw = ComplexObj('Bed (NW/SE)', 29, 1)
        self.complex_obj_wall.add(bed_nw)
        bed_nw.add(self.DIR_SE, 30)

        tent_nw = ComplexObj('Tent (NW/SE)', 79, 1)
        self.complex_obj_wall.add(tent_nw)
        tent_nw.add(self.DIR_E, 80)

        tent_ne = ComplexObj('Tent (NE/SW)', 81, 1)
        self.complex_obj_wall.add(tent_ne)
        tent_ne.add(self.DIR_E, 82)

        wagon = ComplexObj('Wagon', 83, 1)
        self.complex_obj_wall.add(wagon)
        wagon.add(self.DIR_NE, 84)

        self.complex_obj_decal = ComplexObjCollection(self.REV_DIR, 'decalimg')

        # Now premade objects
        self.premade_objects = []

class B2SmartDraw(SmartDraw):
    """
    SmartDraw for Book 2
    """

    book = 2

    def init_vars(self):

        # Various lists to keep track of which objects should be walls
        # Note that water tiles in Book 2 are automatically made seethrough-wall
        # by the engine, so we don't have to specify them here.
        self.wall_list = {}
        self.wall_list['floor_seethrough'] = []
        self.wall_list['decal_blocked'] = [134, 150, 151, 152]
        self.wall_list['decal_seethrough'] = ([59, 74, 75, 91] + range(154, 159) +
            range(170, 174) + range(185, 191) + range(202, 206))
        self.wall_list['wall_blocked'] = ([26, 27, 41, 42, 43, 57, 59, 60, 69, 70, 83, 86, 100, 116, 147] +
            range(256, 267) + [268] + range(272, 283) + [284] + range(286, 298) + range(304, 315) +
            range(320, 332) + range(334, 346) + range(352, 364) + [366] + range(368, 378) +
            range(384, 396) + [400, 401, 406] + range(251, 256))
        self.wall_list['wall_seethrough'] = (range(1, 25) + range(28, 41) +
            range(44, 57) + [58] + range(61, 69) + range(71, 82) + [84, 85] +
            range(87, 97) + [99] + range(101, 107) + range(108, 114) + range(117, 119) +
            range(121, 129) + range(130, 134) + range(136, 147) + range(148, 151) +
            [270, 271] + range(315, 320) + [333] + range(346, 352) +
            [364, 365, 367, 381] + range(396, 400) +
            [407])
        self.wall_list['walldecal_seethrough'] = (range(8, 12) + [81, 97])
        self.wall_list['wall_restrict'] = ([107] + range(298, 304) + [332, 378, 379, 380, 382, 383] +
            range(402, 406))

        # Hardcoded Graphics info
        self.wallstarts = [256, 272, 288, 304, 320, 336, 352, 368, 384]
        self.fenceids = [47, 48, 61, 62, 63, 64]
        # TODO: B2 actually has a couple of sets which could be bigfenced
        self.bigfencestart = 362
        self.special = 301
        self.tilesets = {
                self.IDX_GRASS: [1, 2, 3, 4],
                self.IDX_SAND: [13],
                self.IDX_SNOW: [81, 82, 83, 84],
                self.IDX_LAVA: [109]
            }
        self.random_terrain = [
                [1, 2, 3, 4],      # Regular Grass
                [9, 10, 11, 12],   # Gravelish
                [14, 15],          # Cobbles
                [81, 82, 83, 84],  # Snow
            ]
        self.random_decal = [
                [87, 103, 104],    # Rubble
                [97, 98, 99],      # Smudges
                range(113, 120),   # Bloodstains, small-to-med
                [120, 121],        # Bloodstains, large
                [122, 123],        # Slime?
                [106, 107],        # Starfish
                [181, 182],        # Smashed somethingorother
                [167, 168, 184, 199, 200], # More smashed objects
                [153, 169],        # Strewn papers
                range(209, 213),   # Brown smudge
                [213, 214],        # Snow texture
                [241, 242, 243],   # Cracks
                [72, 88],          # Hay/Straw
                [225, 226, 227],   # Mushrooms
            ]
        self.random_obj = [
                [33, 34],             # Little tropical trees
                [49, 50, 51, 52],     # Smashed chests
                [53, 54],             # Tree Trunks
                [82, 97, 98],         # Watery plants, greenish
                [114, 115],           # Watery plants, yellowish
                [134, 135],           # Mossy overgrowth
                [378, 379],           # Short rocks
                [381, 382],           # Short snowy rocks
                [403, 404],           # Short black rocks
                [251, 252, 253, 255], # Tall Trees
            ]
        self.random_walldecal = [
                [33, 37, 39],   # Wall shadows/smudges (SW->NE)
                [34, 38, 40],   # Wall shadows/smudges (NW->SE)
                [21, 22],       # Cracks (NW->SE)
                [23, 24]        # Cracks (SW->NE)
            ]
        self.water = [ 113 ]

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
        self.add_index(self.IDX_FENCE, 0, self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_FENCE, 1, self.DIR_NE|self.DIR_SW)
        self.add_index(self.IDX_FENCE, 14, self.DIR_SE|self.DIR_NE)
        self.add_index(self.IDX_FENCE, 15, self.DIR_SW|self.DIR_SE)
        self.add_index(self.IDX_FENCE, 16, self.DIR_NE|self.DIR_NW)
        self.add_index(self.IDX_FENCE, 17, self.DIR_NW|self.DIR_SW)

        # "Big" fence Indexes
        self.add_index(self.IDX_BIGFENCE, 0, self.DIR_SW|self.DIR_NE)
        self.add_index(self.IDX_BIGFENCE, 1, self.DIR_NW|self.DIR_SE)

        # Grass Indexes
        self.add_index(self.IDX_GRASS, 1, self.DIR_NE|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 2, self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 3, self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 4, self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 5, self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 6, self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 17, self.DIR_NE)
        self.add_index(self.IDX_GRASS, 18, self.DIR_NW)
        self.add_index(self.IDX_GRASS, 19, self.DIR_SE)
        self.add_index(self.IDX_GRASS, 20, self.DIR_SW)
        self.add_index(self.IDX_GRASS, 33, self.DIR_S|self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 34, self.DIR_N|self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 35, self.DIR_W|self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 36, self.DIR_E|self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 37, self.DIR_N|self.DIR_S)
        self.add_index(self.IDX_GRASS, 49, self.DIR_N)
        self.add_index(self.IDX_GRASS, 50, self.DIR_E)
        self.add_index(self.IDX_GRASS, 51, self.DIR_S)
        self.add_index(self.IDX_GRASS, 52, self.DIR_W)
        self.add_index(self.IDX_GRASS, 53, self.DIR_W|self.DIR_E)
        self.add_index(self.IDX_GRASS, 65, self.DIR_W|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 66, self.DIR_S|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 67, self.DIR_E|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 68, self.DIR_N|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 81, self.DIR_N|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 82, self.DIR_W|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 83, self.DIR_E|self.DIR_NW)
        self.add_index(self.IDX_GRASS, 84, self.DIR_S|self.DIR_NW)

        # Note that these given our current algorithms, will probably never be chosen
        self.add_index(self.IDX_GRASS, 21, self.DIR_N|self.DIR_E|self.DIR_S|self.DIR_W)
        self.add_index(self.IDX_GRASS, 22, self.DIR_N|self.DIR_W)
        self.add_index(self.IDX_GRASS, 38, self.DIR_S|self.DIR_E)
        self.add_index(self.IDX_GRASS, 54, self.DIR_N|self.DIR_E)
        self.add_index(self.IDX_GRASS, 69, self.DIR_NE|self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_GRASS, 70, self.DIR_W|self.DIR_S)
        self.add_index(self.IDX_GRASS, 71, self.DIR_SW|self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_GRASS, 85, self.DIR_NW|self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_GRASS, 86, self.DIR_SE|self.DIR_SW|self.DIR_NW)

        # Sand Indexes
        self.add_index(self.IDX_SAND, 129, self.DIR_NW)
        self.add_index(self.IDX_SAND, 130, self.DIR_NE)
        self.add_index(self.IDX_SAND, 131, self.DIR_SE)
        self.add_index(self.IDX_SAND, 132, self.DIR_SW)
        self.add_index(self.IDX_SAND, 133, self.DIR_SE|self.DIR_NW)
        self.add_index(self.IDX_SAND, 145, self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_SAND, 146, self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_SAND, 147, self.DIR_SE|self.DIR_SW)
        self.add_index(self.IDX_SAND, 148, self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_SAND, 149, self.DIR_NE|self.DIR_SW)

        # Snow Indexes
        self.add_index(self.IDX_SNOW, 230, self.DIR_NW)
        self.add_index(self.IDX_SNOW, 231, self.DIR_NE)
        self.add_index(self.IDX_SNOW, 232, self.DIR_SE)
        self.add_index(self.IDX_SNOW, 233, self.DIR_SW)
        self.add_index(self.IDX_SNOW, 234, self.DIR_NW|self.DIR_SE)
        self.add_index(self.IDX_SNOW, 246, self.DIR_NW|self.DIR_SW)
        self.add_index(self.IDX_SNOW, 247, self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_SNOW, 248, self.DIR_SW|self.DIR_SE)
        self.add_index(self.IDX_SNOW, 249, self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_SNOW, 250, self.DIR_SW|self.DIR_NE)

        # Lava Indexes
        self.add_index(self.IDX_LAVA, 219, self.DIR_NW)
        self.add_index(self.IDX_LAVA, 220, self.DIR_NE)
        self.add_index(self.IDX_LAVA, 221, self.DIR_SE)
        self.add_index(self.IDX_LAVA, 222, self.DIR_SW)
        self.add_index(self.IDX_LAVA, 223, self.DIR_NW|self.DIR_SE)
        self.add_index(self.IDX_LAVA, 235, self.DIR_NW|self.DIR_SW)
        self.add_index(self.IDX_LAVA, 236, self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_LAVA, 237, self.DIR_SW|self.DIR_SE)
        self.add_index(self.IDX_LAVA, 238, self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_LAVA, 239, self.DIR_NE|self.DIR_SW)
        self.add_index(self.IDX_LAVA, 252, self.DIR_SE|self.DIR_SW|self.DIR_NW)
        self.add_index(self.IDX_LAVA, 253, self.DIR_SW|self.DIR_NW|self.DIR_NE)
        self.add_index(self.IDX_LAVA, 254, self.DIR_NW|self.DIR_NE|self.DIR_SE)
        self.add_index(self.IDX_LAVA, 255, self.DIR_NE|self.DIR_SE|self.DIR_SW)

        # Pool to randomly choose from if we're completely surrounded
        self.tile_fullest = {
                self.IDX_GRASS: [69, 71, 85, 86],
                self.IDX_SAND: [133, 149],
                self.IDX_SNOW: [234, 250],
                self.IDX_LAVA: [252, 253, 254, 255],
            }

        # Beach indexes (these are floor tiles, not decals - the directions
        # specified here are the direction that the SAND is in, not the
        # water.  Or to put it another way, these tiles are considered
        # water which happen to bleed into sand a bit.
        self.add_beach_index(114, self.DIR_NW|self.DIR_SW)
        self.add_beach_index(115, self.DIR_NW|self.DIR_NE)
        self.add_beach_index(116, self.DIR_NE|self.DIR_SE)
        self.add_beach_index(117, self.DIR_SW|self.DIR_SE)
        self.add_beach_index(121, self.DIR_E)
        self.add_beach_index(122, self.DIR_S)
        self.add_beach_index(123, self.DIR_W)
        self.add_beach_index(124, self.DIR_N)
        self.add_beach_index(125, self.DIR_NW)
        self.add_beach_index(126, self.DIR_NE)
        self.add_beach_index(127, self.DIR_SE)
        self.add_beach_index(128, self.DIR_SW)
        self.add_beach_index(13, self.DIR_NW|self.DIR_NE|self.DIR_SE|self.DIR_SW)

        # Now smart Complex Objects
        self.complex_obj_floor = ComplexObjCollection(self.REV_DIR, 'floorimg')

        ycarpet1 = ComplexObj('Yellow Carpet (1)', 35)
        self.complex_obj_floor.add(ycarpet1)
        ycarpet1.add(self.DIR_NE, 33)

        ycarpet2 = ComplexObj('Yellow Carpet (2)', 34)
        self.complex_obj_floor.add(ycarpet2)
        ycarpet2.add(self.DIR_NW, 36)

        rcarpet = ComplexObj('Large Red Carpet', 37)
        self.complex_obj_floor.add(rcarpet)
        rcarpet.add(self.DIR_SE, 38)
        rcarpet.add(self.DIR_SW, 39)
        rcarpet.add(self.DIR_NW, 40)

        rcarpet2 = ComplexObj('Small Red Carpet (1)', 41)
        self.complex_obj_floor.add(rcarpet2)
        rcarpet2.add(self.DIR_SW, 43)

        rcarpet3 = ComplexObj('Small Red Carpet (2)', 42)
        self.complex_obj_floor.add(rcarpet3)
        rcarpet3.add(self.DIR_NW, 44)

        self.complex_obj_wall = ComplexObjCollection(self.REV_DIR, 'wallimg')
        
        bed_ne = ComplexObj('Bed (NE/SW)', 1, 1)
        self.complex_obj_wall.add(bed_ne)
        bed_ne.add(self.DIR_NE, 2)

        bed_nw = ComplexObj('Bed (NW/SE)', 3, 1)
        self.complex_obj_wall.add(bed_nw)
        bed_nw.add(self.DIR_SE, 4)

        sickbed = ComplexObj('Sickbed', 122, 1)
        self.complex_obj_wall.add(sickbed)
        sickbed.add(self.DIR_SE, 123)

        tent_nw = ComplexObj('Tent (NW/SE)', 83, 1)
        self.complex_obj_wall.add(tent_nw)
        tent_nw.add(self.DIR_E, 84)

        tent_ne = ComplexObj('Tent (NE/SW)', 85, 1)
        self.complex_obj_wall.add(tent_ne)
        tent_ne.add(self.DIR_E, 86)

        self.complex_obj_decal = ComplexObjCollection(self.REV_DIR, 'decalimg')

        stairs_ne = ComplexObj('Stairs (NE/SW)', 134, 5)
        self.complex_obj_decal.add(stairs_ne)
        stairs_ne.add(self.DIR_SW, 150)

        stairs_ne = ComplexObj('Stairs (NW/SE)', 151, 5)
        self.complex_obj_decal.add(stairs_ne)
        stairs_ne.add(self.DIR_SE, 152)

        # Now premade objects
        self.premade_objects = []

        # Doors!
        for (start, desc, text, cond) in [
                (266, 'Wooden', 'a wooden door.', 550),
                (282, 'Banded', 'a heavy, reinforced door.', 1100)
                ]:
            cur = start
            for (walldecal, dir) in [
                    (19, '/'),
                    (20, '\\')
                    ]:
                for (state, wall, statenum) in [
                        ('Closed', 1, 1),
                        ('Open', 0, 2)
                        ]:
                    obj = PremadeObject('Wooden Door %s - %s' % (dir, state))
                    obj.set_wall(wall)
                    obj.set_wallimg(cur)
                    obj.set_walldecalimg(walldecal)
                    obj.set_script(5)
                    obj.create_scriptobj('random')
                    obj.mapscript.description = text
                    obj.mapscript.state = statenum
                    obj.mapscript.cur_condition = cond
                    obj.mapscript.max_condition = cond
                    self.premade_objects.append(obj)
                    cur += 1

        # Cabinets / Chests
        for (start, desc, text, cond, contents) in [
                (5, 'Small Cabinet', 'an oak cabinet.', 150, 'random'),
                (9, 'Large Cabinet', 'a chest of drawers.', 150, 'random'),
                (17, 'Chest', 'a basic oak chest.', 300, 'random'),
                (21, 'Banded Chest', 'a heavy steel-banded chest.', 800, 'random'),
                (91, 'Metal Chest', 'a massive chest made of a dense, exotic alloy.', 3000, 'random'),
                (124, 'Coffin', 'a pine coffin.', 150, 'empty'),
                ]:
            cur = start
            for dir in [ '\\', '/' ]:
                for (state, statenum) in [
                        ('Closed', 1),
                        ('Open', 2)
                        ]:
                    obj = PremadeObject('%s %s - %s' % (desc, dir, state))
                    obj.set_wall(5)
                    obj.set_wallimg(cur)
                    obj.set_script(2)
                    obj.create_scriptobj(contents)
                    obj.mapscript.description = text
                    obj.mapscript.state = statenum
                    obj.mapscript.cur_condition = cond
                    obj.mapscript.max_condition = cond
                    self.premade_objects.append(obj)
                    cur += 1

        # Misc items
        obj = PremadeObject('Powder Keg')
        obj.set_wall(5)
        obj.set_wallimg(32)
        obj.set_script(15)
        obj.create_scriptobj()
        obj.mapscript.description = 'a keg of black powder.'
        obj.mapscript.cur_condition = 5
        obj.mapscript.max_condition = 5
        self.premade_objects.append(obj)

        obj = PremadeObject('Open Barrel')
        obj.set_wall(5)
        obj.set_wallimg(13)
        obj.set_script(1)
        obj.create_scriptobj()
        obj.mapscript.description = 'a sturdy oaken barrel.'
        obj.mapscript.cur_condition = 80
        obj.mapscript.max_condition = 80
        self.premade_objects.append(obj)

        obj = PremadeObject('Sealed Barrel')
        obj.set_wall(5)
        obj.set_wallimg(14)
        obj.set_script(11)
        obj.create_scriptobj()
        obj.mapscript.description = 'a sturdy oak sealed barrel.'
        obj.mapscript.cur_condition = 90
        obj.mapscript.max_condition = 90
        self.premade_objects.append(obj)

        obj = PremadeObject('Well')
        obj.set_wall(1)
        obj.set_wallimg(57)
        obj.set_script(16)
        obj.create_scriptobj()
        obj.mapscript.description = 'a well.'
        self.premade_objects.append(obj)

        for (id, dir) in [(39, '\\'), (40, '/')]:
            obj = PremadeObject('Archery Target %s' % (dir))
            obj.set_wall(1)
            obj.set_wallimg(id)
            obj.set_script(17)
            obj.create_scriptobj()
            obj.mapscript.description = 'a target.'
            self.premade_objects.append(obj)

        for (id, dir) in [(2, '/'), (4, '\\')]:
            obj = PremadeObject('Sconce %s' % (dir))
            obj.set_walldecalimg(id)
            obj.set_script(12)
            obj.create_scriptobj()
            obj.mapscript.description = 'a sconce.'
            self.premade_objects.append(obj)

        # Levers
        cur = 65
        for dir in ['\\', '/']:
            for (text, toggle) in [('Up', 4), ('Toggled', 5)]:
                obj = PremadeObject('Lever (%s) %s' % (text, dir))
                obj.set_wall(5)
                obj.set_wallimg(cur)
                obj.set_script(7)
                obj.create_scriptobj()
                obj.mapscript.description = 'a wooden lever.'
                obj.mapscript.state = toggle
                self.premade_objects.append(obj)
                cur += 1
