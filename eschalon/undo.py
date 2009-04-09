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

class UndoHistory(object):
    """
    Undo data for single edit.
    """

    def __init__(self, map, x, y):
        """ A new object, the 'old' square is required. """
        self.x = x
        self.y = y
        self.oldsquare = map.squares[y][x].replicate()
        (self.old_entidx, self.old_scriptidx) = self.grab_idx(map, map.squares[y][x])

    def set_new(self, map):
        """ Update this record's 'new' square record """
        newsquare = map.squares[self.y][self.x]
        self.newsquare = newsquare.replicate()
        (self.new_entidx, self.new_scriptidx) = self.grab_idx(map, newsquare)

    def grab_idx(self, map, square):
        """
        Given a map and a square, return a tuple containing the index of
        the square's entity (if appropriate) and a list of indexes of the
        square's scripts (if appropriate)
        """
        entidx = None
        scriptidxes = []
        if (square.entity):
            if (square.entity in map.entities):
                entidx = map.entities.index(square.entity)
            else:
                raise Exception('Entity in square not linked in master map list')
        scriptcount = 0
        for script in square.scripts:
            scriptcount += 1
            if (script in map.scripts):
                scriptidxes.append(map.scripts.index(script))
            else:
                raise Exception('Script %d in square not linked in master map list' % (scriptcount))
        return (entidx, scriptidxes)

class Undo(object):
    """
    A class to hold historical editing information, for undo purposes.
    """

    def __init__(self, map):
        self.history = []
        self.maxstack = 50
        self.curidx = -1
        self.map = map

    def have_undo(self):
        return (self.curidx >= 0)

    def have_redo(self):
        return (self.curidx < len(self.history)-1)

    def store(self, x, y):
        self.curidx += 1
        self.history.insert(self.curidx, UndoHistory(self.map, x, y))
        del self.history[self.curidx+1:]
        if (len(self.history) > self.maxstack):
            del self.history[0]

    def set_new(self):
        if (self.have_undo()):
            self.history[self.curidx].set_new(self.map)

    def undo(self):
        if (self.have_undo()):
            self.curidx -= 1
            obj = self.history[self.curidx+1]
            self.process_changes(obj.x, obj.y, obj.oldsquare,
                    obj.new_entidx, obj.new_scriptidx,
                    obj.old_entidx, obj.old_scriptidx)
            return (obj.x, obj.y)
        else:
            return None

    def redo(self):
        if (self.have_redo()):
            self.curidx += 1
            obj = self.history[self.curidx]
            self.process_changes(obj.x, obj.y, obj.newsquare,
                    obj.old_entidx, obj.old_scriptidx,
                    obj.new_entidx, obj.new_scriptidx)
            return (obj.x, obj.y)
        else:
            return None

    def process_changes(self, x, y, tosquare, from_entidx, from_scriptidx, to_entidx, to_scriptidx):
        """
        Actually make the change in self.map, given from/to vars.  Mostly
        this is just necessary so that our entity and script links stay
        populated like they should.
        """
        # First update the map square itself
        self.map.squares[y][x] = tosquare.replicate()

        # Entity first
        if (from_entidx and from_entidx >= 0):
            del self.map.entities[from_entidx]
        if (to_entidx and to_entidx >= 0):
            self.map.entities.insert(to_entidx, self.map.squares[y][x].entity)

        # ... and now Scripts
        idxes = from_scriptidx[:]
        idxes.reverse()
        for idx in idxes:
            del self.map.scripts[idx]
        for (i, idx) in enumerate(to_scriptidx):
            self.map.scripts.insert(idx, self.map.squares[y][x].scripts[i])
