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

from eschalonb1.map import Map

class SmartDraw(object):
    """ A class to deal with "smart" drawing functions. """

    CONN_NE = 0x01
    CONN_SE = 0x02
    CONN_SW = 0x04
    CONN_NW = 0x08

    REV_CONN = {
            CONN_NE: CONN_SW,
            CONN_SE: CONN_NW,
            CONN_SW: CONN_NE,
            CONN_NW: CONN_SE
        }

    def __init__(self):
        self.wallstarts = [161, 171, 181, 191, 201]
        self.special = 213
        self.map = None
        self.indexes = {}
        self.revindexes = {}
        self.add_index(-1, self.CONN_NE|self.CONN_SE|self.CONN_SW|self.CONN_NW)
        self.add_index(0, self.CONN_NE|self.CONN_SW)
        self.add_index(1, self.CONN_SE|self.CONN_NW)
        self.add_index(2, self.CONN_SE|self.CONN_SW)
        self.add_index(3, self.CONN_SW|self.CONN_NW)
        self.add_index(4, self.CONN_NE|self.CONN_NW)
        self.add_index(5, self.CONN_NE|self.CONN_SE)
        self.add_index(6, self.CONN_SE|self.CONN_SW|self.CONN_NW)
        self.add_index(7, self.CONN_NE|self.CONN_SW|self.CONN_NW)
        self.add_index(8, self.CONN_NE|self.CONN_SE|self.CONN_NW)
        self.add_index(9, self.CONN_NE|self.CONN_SE|self.CONN_SW)

    def add_index(self, index, connections):
        self.indexes[index] = connections
        self.revindexes[connections] = index

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
        return None

    def draw_wall(self, square):
        """
        Draws using the given wall.
        Will return a list of squares that have been updated by this action
        (not including the given square, which is assumed).
        """
        # First set up and make sure that we're even drawing a wall
        retarr = []
        wallgroup = self.get_wall_group(square)
        if (wallgroup is None):
            return retarr

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
        if (connflags not in self.revindexes):
            if (flagcount == 0):
                connflags = self.indexes[0]
            elif (flagcount == 1):
                if ((connflags & self.CONN_NE) == self.CONN_NE or
                    (connflags & self.CONN_SW) == self.CONN_SW):
                    connflags = self.indexes[0]
                else:
                    connflags = self.indexes[1]
            else:
                raise Exception("flagcount isn't 1 or 0 - should figure out why")

        # TODO: this is duplicated in add_wall_connection...
        if (self.revindexes[connflags] == -1):
            square.wallimg = self.special
        else:
            square.wallimg = wallgroup + self.revindexes[connflags]

        # And lastly, return.
        return retarr

    def add_wall_connection(self, group, square, dir):
        """
        Adds a connection to the given square.  Note that this doesn't do
        any actual bounds checking; it should really only be called from
        connect(), above.  Returns whether or not we modified the square.

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
        curflags = self.indexes[idx]
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
            if (self.revindexes[newflags] == -1):
                square.wallimg = self.special
            else:
                square.wallimg = group + self.revindexes[newflags]
            return True

