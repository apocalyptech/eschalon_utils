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

class Additional(object):
    """
    When keeping track of one tile for an undo action, it's possible that
    the change for that tile triggers changes in other tiles (for smart
    wall drawing, for instance).  This class keeps track of extra information
    which may change for a given additional tile.

    Note that it does *not* keep the whole square structure; just a few
    attributes that we'll be modifying.
    """

    def __init__(self, square):
        self.x = square.x
        self.y = square.y
        self.old_decalimg = square.decalimg
        self.old_wallimg = square.wallimg
        self.new_decalimg = self.old_decalimg
        self.new_wallimg = self.old_wallimg
        self.square = square

    def set_new(self):
        """
        Sets our "new" variables from our given square, and
        return True if we've changed, or False if we haven't.

        Note that we invalidate our own internal 'square' object
        so that we don't accidentally try to use it later.  Our
        reference to that object may become invalid later on
        due to outside undo/redo activity.
        """
        self.new_decalimg = self.square.decalimg
        self.new_wallimg = self.square.wallimg
        self.square = None
        return (self.new_decalimg != self.old_decalimg or
                self.new_wallimg != self.old_wallimg)

    def undo(self, square):
        """
        Process an undo action on this one square.
        """
        square.decalimg = self.old_decalimg
        square.wallimg = self.old_wallimg

    def redo(self, square):
        """
        Process a redo action on this one square.
        """
        square.decalimg = self.new_decalimg
        square.wallimg = self.new_wallimg

class UndoHistory(object):
    """
    Undo data for single edit.
    """

    def __init__(self, map, x, y):
        """ A new object, the 'old' square is required. """
        self.x = x
        self.y = y
        self.text = 'Edit'
        self.additional = []
        self.mainchanged = False
        self.oldsquare = map.squares[y][x].replicate()
        (self.old_entidx, self.old_scriptidx) = self.grab_idx(map, map.squares[y][x])

    def set_new(self, map):
        """ Update this record's 'new' square record """
        retval = False

        # First loop through any "additional" squares, to see
        # if they've changed.  Also prune the list of squares
        # which didn't change.
        newadditional = []
        for add_obj in self.additional:
            if (add_obj.set_new()):
                newadditional.append(add_obj)
                retval = True
        self.additional = newadditional

        # ... and now check our main square
        newsquare = map.squares[self.y][self.x]
        if (not self.oldsquare.equals(newsquare)):
            self.newsquare = newsquare.replicate()
            (self.new_entidx, self.new_scriptidx) = self.grab_idx(map, newsquare)
            self.mainchanged = True
            retval = True

        # Return
        return retval

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

    def set_text(self, text):
        self.text = text

    def add_additional(self, square):
        """
        Adds an additional square that was changed (possibly)
        along with our main square.
        """
        if (square):
            self.additional.append(Additional(square))

class Undo(object):
    """
    A class to hold historical editing information, for undo purposes.
    """

    def __init__(self, map):
        self.history = []
        self.maxstack = 50
        self.curidx = -1
        self.map = map
        self.finished = True

    def have_undo(self):
        """ Report whether there are any undos in the stack """
        return (self.curidx >= 0)

    def have_redo(self):
        """ Report whether there are any redos in the stack """
        return (self.curidx < len(self.history)-1)

    def get_undo(self):
        """ Gets the next "undo" action.  Used primarily for changing menu text. """
        if (self.have_undo()):
            return self.history[self.curidx]
        else:
            return None

    def get_redo(self):
        """ Gets the next "redo" action.  Used primarily for changing menu text. """
        if (self.have_redo()):
            return self.history[self.curidx+1]
        else:
            return None

    def store(self, x, y):
        """
        Stores the current map state as the "old" square in the
        actual History object.  This level-of-undo is not considered
        finished until finish() is called later.
        """
        if (self.finished):
            self.curidx += 1
            self.history.insert(self.curidx, UndoHistory(self.map, x, y))
            self.finished = False
        else:
            raise Exception('Previous undo must be finished before storing a new one')

    def finish(self):
        """
        Finishes off the undo level by setting the "new" square in
        the actual History object.  If the new square isn't any different
        from the old one, back out the undo level.

        Returns True if the relevant square has been changed (and thus the
        undo state has been altered), or False if no changes have been made.
        """
        if (self.have_undo()):
            if (self.history[self.curidx].set_new(self.map)):
                del self.history[self.curidx+1:]
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

    def add_additional(self, square):
        """
        Adds an additional square to our current History. """
        if (self.finished):
            raise Exception('add_additional() must be called before finish()')
        else:
            self.history[self.curidx].add_additional(square)

    def undo(self):
        """
        Process an undo action.
        Returns a list of coordinate pairs which need updating.
        """
        if (self.have_undo()):
            self.curidx -= 1
            obj = self.history[self.curidx+1]
            retval = []
            if (obj.mainchanged):
                self.process_changes(obj.x, obj.y, obj.oldsquare,
                        obj.new_entidx, obj.new_scriptidx,
                        obj.old_entidx, obj.old_scriptidx)
                retval.append((obj.x, obj.y))
            for add_obj in self.history[self.curidx+1].additional:
                add_obj.undo(self.map.squares[add_obj.y][add_obj.x])
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
                self.process_changes(obj.x, obj.y, obj.newsquare,
                        obj.old_entidx, obj.old_scriptidx,
                        obj.new_entidx, obj.new_scriptidx)
                retval.append((obj.x, obj.y))
            for add_obj in self.history[self.curidx].additional:
                add_obj.redo(self.map.squares[add_obj.y][add_obj.x])
                retval.append((add_obj.x, add_obj.y))
            return retval
        else:
            return []

    def process_changes(self, x, y, tosquare, from_entidx, from_scriptidx, to_entidx, to_scriptidx):
        """
        Actually make the change in self.map, given from/to vars.  Mostly
        this is just necessary so that our entity and script links stay
        populated like they should.
        """

        # First update the map square itself
        self.map.squares[y][x] = tosquare.replicate()

        # Entity first
        if (from_entidx is not None and from_entidx >= 0):
            del self.map.entities[from_entidx]
        if (to_entidx is not None and to_entidx >= 0):
            self.map.entities.insert(to_entidx, self.map.squares[y][x].entity)

        # ... and now Scripts
        idxes = from_scriptidx[:]
        idxes.reverse()
        for idx in idxes:
            del self.map.scripts[idx]
        for (i, idx) in enumerate(to_scriptidx):
            self.map.scripts.insert(idx, self.map.squares[y][x].scripts[i])

    # TODO: Delete this before release
    def report(self):
        """
        This just prints out some text to the console, used for making sure
        that stuff is working how it should.
        """
        print '%d total scripts in map' % (len(self.map.scripts))
        scriptcounters = {}
        for script in self.map.scripts:
            squareval = script.y*100+script.x
            if (squareval not in scriptcounters):
                scriptcounters[squareval] = -1
            scriptcounters[squareval] += 1
            squarescript = self.map.squares[script.y][script.x].scripts[scriptcounters[squareval]]
            if (squarescript == script):
                matched = 'matched'
            else:
                matched = 'DOES NOT MATCH'
            print ' * (%d, %d), script %d, %s' % (script.x, script.y, scriptcounters[squareval]+1, matched)
        print
        print '%d total entities in map' % (len(self.map.entities))
        for entity in self.map.entities:
            squareentity = self.map.squares[entity.y][entity.x].entity
            if (squareentity == entity):
                matched = 'matched'
            else:
                matched = 'DOES NOT MATCH'
            print ' * (%d, %d), %s' % (entity.x, entity.y, matched)
        print
