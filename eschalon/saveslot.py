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


import os
import time
import glob
from eschalon.map import Map
from eschalon.savefile import Savefile, LoadException
from eschalon.savename import Savename


class SaveslotMap(object):
    """
    Simple class to hold some information about maps stored within a
    save slot.  Effectively just a well-defined dict.
    """

    def __init__(self, filename, mapname, book):
        self.filename = filename
        self.mapname = mapname
        self.book = book

    def filename_short(self):
        return os.path.basename(self.filename)


class Saveslot(object):
    """
    Class to hold some information about a savegame slot.  Mostly just
    to be used on the "open map" dialog for savegames.  This will raise
    a savefile.LoadException if there are any problems loading the
    directory (such as if it's not a proper save slot)

    By default this will not scan for map files, or load in the character
    name, but if you pass load_all=True, it will do so.  Passing "book"
    along with load_all=True will allow the character name to be loaded
    even if there are no map files present to autodetect the book number.

    The "savename" file for Books 1+2+3 all start with a string containing
    the user-set name of the savefile, so there's currently no need to
    divide this out based on book.
    """

    def __init__(self, directory, load_all=False, book=None):
        """ Empty object. """
        self.directory = directory

        # Make sure we really are a directory
        if not os.path.isdir(directory):
            raise LoadException('%s is not a directory' % (directory))

        # Store our modification time
        self.timestamp_epoch = os.path.getmtime(directory)
        self.timestamp = time.strftime(
            '%a %b %d, %Y, %I:%M %p', time.gmtime(self.timestamp_epoch))

        # Find the save name
        self.savename_loc = os.path.join(directory, 'savename')
        if not os.path.exists(self.savename_loc):
            raise LoadException(
                '"savename" file not found in %s' % (directory))
        self.savenameobj = Savename.load(self.savename_loc)
        self.savenameobj.read()
        self.savename = self.savenameobj.savename

        # Set up our charname values
        self.char_loc = os.path.join(directory, 'char')
        self.charname = 'n/a'
        self.char_loaded = False

        # Set up our map list
        self.maps = []
        self.maps_loaded = False

        # Load all information if asked
        if load_all:
            self.load_maps()
            if book is None:
                try:
                    self.load_charname()
                except LoadException:
                    # We'll just do without the charname in this case
                    pass
            else:
                # We'll allow the exception if we're expecting a particular
                # book
                self.load_charname(book)

    def load_maps(self):
        """
        Read our collection of maps from the dir
        """
        self.maps = []
        self.maps_loaded = True
        map_filenames = sorted(
            glob.glob(os.path.join(self.directory, '*.map')))
        for map_filename in map_filenames:
            try:
                (book, mapname, df) = Map.get_mapinfo(map_filename)
                self.maps.append(SaveslotMap(map_filename, mapname, book))
            except:
                # Don't bother reporting, don't think it's worth it for our
                # typical use cases
                pass

    def load_charname(self, book=None):
        """
        Read our character name; this is a bit dependant on the book number,
        which is why we pass it in here.  If the book number is not passed
        in, we will scan for map files and then use the first map's book
        number.  If there are no maps in the slot, then we'll raise a
        LoadException
        """

        # First figure out which book number we are, if we don't have it yet
        if not book:
            if not self.maps_loaded:
                self.load_maps()
            if len(self.maps) > 0:
                book = self.maps[0].book
            else:
                raise LoadException(
                    'Could not auto-detect which book version to use for charname')

        # Now do the actual loading
        if not os.path.exists(self.char_loc):
            raise LoadException('"char" file not found in %s' % (directory))
        df = Savefile(self.char_loc)
        df.open_r()
        if book == 1:
            df.readint()
        else:
            df.readuchar()
        self.charname = df.readstr()
        self.char_loaded = True
        df.close()

    def print_info(self):
        """
        Will print our information out to the console.  Only really useful
        for debugging.
        """
        print('Slot: %s' % (self.directory))
        print('Save Name: %s' % (self.savename))
        print('Character Name: %s' % (self.charname))
        if self.maps_loaded:
            print('Maps:')
            for esch_map in self.maps:
                print(' * %s - %s' %
                      (esch_map.filename_short(), esch_map.mapname))
        else:
            print('(Maps have not been loaded yet)')
        print()

    def slotname_short(self):
        """
        Returns only the slot number portion of the dir
        """
        return os.path.basename(self.directory)

    def __cmp__(self, b):
        """
        Can be used for sorting so that "slot2" comes after "slot1", instead of "slot11"
        """
        a_short = self.slotname_short()
        b_short = b.slotname_short()
        try:
            if (a_short[:4] == 'slot' and
                str(int(a_short[4:])) == a_short[4:] and
                b_short[:4] == 'slot' and
                str(int(b_short[4:])) == b_short[4:]
                ):
                return cmp(int(a_short[4:]), int(b_short[4:]))
        except ValueError:
            pass

        return cmp(a_short, b_short)
