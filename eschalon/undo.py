#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2014 CJ Kucera, Elliot Kendall
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
import logging
LOG = logging.getLogger(__name__)


class Additional(object):
    """
    When keeping track of one tile for an undo action, it's possible that
    the change for that tile triggers changes in other tiles (for smart
    wall drawing, for instance).  This class keeps track of extra information
    which may change for a given additional tile.

    Note that it does *not* keep the whole tile structure; just a few
    attributes that we'll be modifying.
    """

    # TODO: For now, nothing which uses this touches tilecontents.  Something
    # may end up doing that in the future, though.  If so, make sure to
    # update this.

    def __init__(self, tile):
        self.x = tile.x
        self.y = tile.y
        self.old_wall = tile.wall
        self.old_walldecalimg = tile.walldecalimg
        self.old_decalimg = tile.decalimg
        self.old_wallimg = tile.wallimg
        self.old_floorimg = tile.floorimg
        self.new_wall = self.old_wall
        self.new_walldecalimg = self.old_walldecalimg
        self.new_decalimg = self.old_decalimg
        self.new_wallimg = self.old_wallimg
        self.new_floorimg = self.old_floorimg
        self.tile = tile

    def set_new(self):
        """
        Sets our "new" variables from our given tile, and
        return True if we've changed, or False if we haven't.

        Note that we invalidate our own internal 'tile' object
        so that we don't accidentally try to use it later.  Our
        reference to that object may become invalid later on
        due to outside undo/redo activity.
        """
        self.new_wall = self.tile.wall
        self.new_decalimg = self.tile.decalimg
        self.new_wallimg = self.tile.wallimg
        self.new_floorimg = self.tile.floorimg
        self.new_walldecalimg = self.tile.walldecalimg
        self.tile = None
        return (self.new_wall != self.old_wall or
                self.new_decalimg != self.old_decalimg or
                self.new_wallimg != self.old_wallimg or
                self.new_floorimg != self.old_floorimg or
                self.new_walldecalimg != self.old_walldecalimg)

    def undo(self, tile):
        """
        Process an undo action on this one tile.
        """
        tile.wall = self.old_wall
        tile.walldecalimg = self.old_walldecalimg
        tile.decalimg = self.old_decalimg
        tile.wallimg = self.old_wallimg
        tile.floorimg = self.old_floorimg

    def redo(self, tile):
        """
        Process a redo action on this one tile.
        """
        tile.wall = self.new_wall
        tile.walldecalimg = self.new_walldecalimg
        tile.decalimg = self.new_decalimg
        tile.wallimg = self.new_wallimg
        tile.floorimg = self.new_floorimg


class UndoHistory(object):
    """
    Undo data for single edit.
    """

    def __init__(self, map, x, y):
        """ A new object, the 'old' tile is required. """
        self.x = x
        self.y = y
        self.text = 'Edit'
        self.additional = []
        self.mainchanged = False
        self.oldtile = map.tiles[y][x].replicate()
        (self.old_entidx, self.old_tilecontentidx) = self.grab_idx(
            map, map.tiles[y][x])

    def set_new(self, map):
        """ Update this record's 'new' tile record """
        retval = False

        # First loop through any "additional" tiles, to see
        # if they've changed.  Also prune the list of tiles
        # which didn't change.
        newadditional = []
        for add_obj in self.additional:
            if (add_obj.set_new()):
                newadditional.append(add_obj)
                retval = True
        self.additional = newadditional

        # ... and now check our main tile
        newtile = map.tiles[self.y][self.x]
        if (not self.oldtile.equals(newtile)):
            self.newtile = newtile.replicate()
            (self.new_entidx, self.new_tilecontentidx) = self.grab_idx(map, newtile)
            self.mainchanged = True
            retval = True

        # Return
        return retval

    def grab_idx(self, map, tile):
        """
        Given a map and a tile, return a tuple containing the index of
        the tile's entity (if appropriate) and a list of indexes of the
        tile's tilecontents (if appropriate)
        """
        entidx = None
        tilecontentidxes = []
        if (tile.entity):
            if (tile.entity in map.entities):
                entidx = map.entities.index(tile.entity)
            else:
                raise Exception('Entity in tile not linked in master map list')
        tilecontentcount = 0
        for tilecontent in tile.tilecontents:
            tilecontentcount += 1
            if (tilecontent in map.tilecontents):
                tilecontentidxes.append(map.tilecontents.index(tilecontent))
            else:
                raise Exception(
                    'Script %d in tile not linked in master map list' % (tilecontentcount))
        return (entidx, tilecontentidxes)

    def set_text(self, text):
        self.text = text

    def add_additional(self, tile):
        """
        Adds an additional tile that was changed (possibly)
        along with our main tile.
        """
        if (tile):
            self.additional.append(Additional(tile))


class Undo(object):
    """
    A class to hold historical editing information, for undo purposes.
    """

    def __init__(self, mapobj):
        self.history = []
        self.maxstack = 50
        self.curidx = -1
        self.mapobj = mapobj
        self.finished = True

    def have_undo(self):
        """ Report whether there are any undos in the stack """
        return (self.curidx >= 0)

    def have_redo(self):
        """ Report whether there are any redos in the stack """
        return (self.curidx < len(self.history) - 1)

    def get_undo(self):
        """ Gets the next "undo" action.  Used primarily for changing menu text. """
        if (self.have_undo()):
            return self.history[self.curidx]
        else:
            return None

    def get_redo(self):
        """ Gets the next "redo" action.  Used primarily for changing menu text. """
        if (self.have_redo()):
            return self.history[self.curidx + 1]
        else:
            return None

    def store(self, x, y):
        """
        Stores the current map state as the "old" tile in the
        actual History object.  This level-of-undo is not considered
        finished until finish() is called later.
        """
        if (self.finished):
            self.curidx += 1
            self.history.insert(self.curidx, UndoHistory(self.mapobj, x, y))
            self.finished = False
        else:
            raise Exception(
                'Previous undo must be finished before storing a new one')

    def finish(self):
        """
        Finishes off the undo level by setting the "new" tile in
        the actual History object.  If the new tile isn't any different
        from the old one, back out the undo level.

        Returns True if the relevant tile has been changed (and thus the
        undo state has been altered), or False if no changes have been made.
        """
        if (self.have_undo()):
            if (self.history[self.curidx].set_new(self.mapobj)):
                del self.history[self.curidx + 1:]
                if (len(self.history) > self.maxstack):
                    del self.history[0]
                    self.curidx -= 1
                retval = True
            else:
                del self.history[self.curidx]
                self.curidx -= 1
                retval = False
            self.finished = True
            return retval
        else:
            raise Exception('store() must be called before finish()')

    def cancel(self):
        """
        Cancels out of an Undo record.  This will basically be triggered when
        a drawing function triggers an Exception.  If cancel() is called, further
        editing actions can be made to the map.  Otherwise, the app would be
        forever stuck in a non-editable state.  (Which may not be a bad idea
        honestly, but what the hell, right?)

        Note that it's possible (even likely) that the map will have been
        changed during the drawing action, so cancelling an Undo will NOT
        revert the map to how it was when we started.
        """
        if (self.have_undo()):
            del self.history[self.curidx]
            self.curidx -= 1
            self.finished = True
            return True
        else:
            raise Exception('There is no unfinished Undo action to cancel')

    def set_text(self, text):
        """
        Sets the label of the current undo action, to provide better text in
        the menus.
        """
        if (self.finished):
            raise Exception('set_text() must be called before finish()')
        else:
            self.history[self.curidx].set_text(text)

    def add_additional(self, tile):
        """
        Adds an additional tile to our current History. """
        if (self.finished):
            raise Exception('add_additional() must be called before finish()')
        else:
            self.history[self.curidx].add_additional(tile)

    def undo(self):
        """
        Process an undo action.
        Returns a list of coordinate pairs which need updating.
        """
        if (self.have_undo()):
            self.curidx -= 1
            obj = self.history[self.curidx + 1]
            retval = []
            if (obj.mainchanged):
                self.process_changes(obj.x, obj.y, obj.oldtile,
                                     obj.new_entidx, obj.new_tilecontentidx,
                                     obj.old_entidx, obj.old_tilecontentidx)
                retval.append((obj.x, obj.y))
            for add_obj in self.history[self.curidx + 1].additional:
                add_obj.undo(self.mapobj.tiles[add_obj.y][add_obj.x])
                retval.append((add_obj.x, add_obj.y))
            return retval
        else:
            return []

    def redo(self):
        """
        Process a redo action.
        Returns a list of coordinate pairs which need updating.
        """
        if (self.have_redo()):
            self.curidx += 1
            obj = self.history[self.curidx]
            retval = []
            if (obj.mainchanged):
                self.process_changes(obj.x, obj.y, obj.newtile,
                                     obj.old_entidx, obj.old_tilecontentidx,
                                     obj.new_entidx, obj.new_tilecontentidx)
                retval.append((obj.x, obj.y))
            for add_obj in self.history[self.curidx].additional:
                add_obj.redo(self.mapobj.tiles[add_obj.y][add_obj.x])
                retval.append((add_obj.x, add_obj.y))
            return retval
        else:
            return []

    def process_changes(self, x, y, totile, from_entidx, from_tilecontentidx, to_entidx, to_tilecontentidx):
        """
        Actually make the change in self.mapobj, given from/to vars.  Mostly
        this is just necessary so that our entity and tilecontent links stay
        populated like they should.
        """

        # First update the map tile itself
        self.mapobj.tiles[y][x] = totile.replicate()

        # Entity first
        if (from_entidx is not None and from_entidx >= 0):
            del self.mapobj.entities[from_entidx]
        if (to_entidx is not None and to_entidx >= 0):
            self.mapobj.entities.insert(
                to_entidx, self.mapobj.tiles[y][x].entity)

        # ... and now Scripts
        idxes = from_tilecontentidx[:]
        idxes.reverse()
        for idx in idxes:
            del self.mapobj.tilecontents[idx]
        for (i, idx) in enumerate(to_tilecontentidx):
            self.mapobj.tilecontents.insert(
                idx, self.mapobj.tiles[y][x].tilecontents[i])

    def report(self):
        """
        This just prints out some text to the console, used for making sure
        that stuff is working how it should.  Note that this isn't really maintained
        at all since I just used it for debugging while figuring things out, so it
        may very well fail right now.  Nothing in the code actually calls this.
        """
        print('%d total tilecontents in map' % (len(self.mapobj.tilecontents)))
        tilecontentcounters = {}
        for tilecontent in self.mapobj.tilecontents:
            tileval = tilecontent.y * 100 + tilecontent.x
            if (tileval not in tilecontentcounters):
                tilecontentcounters[tileval] = -1
            tilecontentcounters[tileval] += 1
            tiletilecontent = self.mapobj.tiles[tilecontent.y][tilecontent.x].tilecontents[tilecontentcounters[tileval]]
            if (tiletilecontent == tilecontent):
                matched = 'matched'
            else:
                matched = 'DOES NOT MATCH'
            print(' * (%d, %d), tilecontent %d, %s' % (tilecontent.x,
                                                       tilecontent.y, tilecontentcounters[tileval] + 1, matched))
        print()
        print('%d total entities in map' % (len(self.mapobj.entities)))
        for entity in self.mapobj.entities:
            tileentity = self.mapobj.tiles[entity.y][entity.x].entity
            if (tileentity == entity):
                matched = 'matched'
            else:
                matched = 'DOES NOT MATCH'
            print(' * (%d, %d), %s' % (entity.x, entity.y, matched))
        print()
