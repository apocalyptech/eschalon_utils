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

import struct
from eschalon import constants as c
from eschalon.savefile import Savefile, LoadException
from eschalon.constantsb1 import B1Constants

class Savename(object):
    book = None

    def __init__(self, df):
        """ A fresh object. """

        self.savename = ''
        self.savedate = ''
        self.savetime = ''
        self.mapname = ''
        self.totalsecs = 0
        self.totalturns = 0
        self.totaldays = 0
        self.coloration = 0
        self.narratives = [] # Has the player seen this narrative? 0=no, 1=yes
        self.quests = []
        self.npcs = [] # Has the player talked to this NPC? 0=no, 1=yes
        self.quicktravel = 0
        self.options = [] # volume controls, tactical grid, etc.
        self.unknowns = []
        self.df = df

    def replicate(self):
        newsn = Savename.load(self.df.filename, self.book)

        if self.book == 1:
            newsn = B1Savename(Savefile(self.df.filename))
        elif self.book == 2:
            newsn = B2Savename(Savefile(self.df.filename))
        elif self.book == 3:
            newsn = B3Savename(Savefile(self.df.filename))

        # Single vals (no need to do actual replication)
        newsn.savename = self.savename
        newsn.savedate = self.savedate
        newsn.savetime = self.savetime
        newsn.mapname = self.mapname
        newsn.totalsecs = self.totalsecs
        newsn.totalturns = self.totalturns
        newsn.totaldays = self.totaldays
        newsn.coloration = self.coloration
        newsn.quicktravel = self.quicktravel

        # Lists that need copying
        for val in self.options:
            newsn.options.append(val)
        for val in self.narratives:
            newsn.narratives.append(val)
        for val in self.quests:
            newsn.quests.append(val)
        for val in self.npcs:
            newsn.npcs.append(val)

        # Call out to the subclass replication function
        self._sub_replicate(newsn)

        # Now return our duplicated object
        return newsn

    def _sub_replicate(self, newsn):
        """
        Just a stub function for superclasses to override, to replicate any
        superclass-specific data
        """
        pass

    def write(self):
        raise NotImplementedError('Writing savenames is not currently supported')

    @staticmethod
    def load(filename, book=None, req_book=None):
        """
        Static method to load a savename file.  This will open the file once and
        read in a bit of data to determine whether this is a Book 1 character file or
        a Book 2 character file, and then call the appropriate constructor and
        return the object.  The individual Book constructors expect to be passed in
        an 
        """
        df = Savefile(filename)

        # First figure out what format to load, if needed
        if book is None:
            try:
                df.open_r()
                name = df.readstr()
                date = df.readstr()
                time = df.readstr()
                map_or_version = df.readstr()
                df.close()
            except (IOError, struct.error), e:
                raise LoadException(str(e))

            if map_or_version.startswith('book3'):
                book = 3
            elif map_or_version in B1Constants.maps:
                book = 1
            else:
                book = 2

        # See if we're required to conform to a specific book
        if (req_book is not None and book != req_book):
            raise LoadException('This utility can only load Book %d Character files; this file is from Book %d' % (req_book, book))

        # Now actually return the object
        if book == 1:
            c.switch_to_book(1)
            return B1Savename(df)
        elif book == 2:
            c.switch_to_book(2)
            return B2Savename(df)
        else:
            c.switch_to_book(3)
            return B3Savename(df)

class B1Savename(Savename):
    """
    Book 1 Character definitions
    """

    book = 1

    def __init__(self, df):
        super(B1Savename, self).__init__(df)

        # Book 1 specific vars

    def read(self):
        """ Read in the whole save file from a file descriptor. """

        try:
            # Open the file
            self.df.open_r()

            # This is the most guesswork of the three books since it's
            # farthest from the B3 format.  It's also harder to tell where
            # sections begin and end since everything's a 4-byte int.  Not
            # well checked, probably has bugs.
            self.savename = self.df.readstr()
            self.savedate = self.df.readstr()
            self.savetime = self.df.readstr()
            self.mapname = self.df.readstr()
            self.totalsecs = self.df.readint()
            self.totalturns = self.df.readint()
            self.totaldays = self.df.readint()
            self.coloration = self.df.readint()
            for i in range(10):
                self.options.append(self.df.readint())
            for i in range(255):
                self.narratives.append(self.df.readint())
            for i in range(150):
                self.quests.append(self.df.readint())

            # Close the file
            self.df.close()

        except (IOError, struct.error), e:
            raise LoadException(str(e))

    def _sub_replicate(self, newsn):
        """
        Replicate our Book 1 specific data
        """

class B2Savename(Savename):
    """
    Book 2 Character definitions
    """

    book = 2

    def __init__(self, df):
        super(B2Savename, self).__init__(df)

        # Book 2 specific vars
        self.combatmode = 0
        self.rules = 0
        self.seed = 0
        self.challenges = 0
        self.stats = []
        self.weather_type = 0
        self.weather_duration = 0
        self.weather_start = 0
        self.weather_next = 0
        self.cloud_darkener = 0
        self.cloud_alpha = 0
        self.weather_number = 0
        self.weather_active = 0

    def read(self):
        """ Read in the whole save file from a file descriptor. """

        try:
            # Open the file
            self.df.open_r()

            # Based on BW's B3 spec and looking at the file manually. 
            # Oddly, lines up better than the B3 format.  Not well checked,
            # though, and probably has bugs
            self.savename = self.df.readstr()
            self.savedate = self.df.readstr()
            self.savetime = self.df.readstr()
            self.mapname = self.df.readstr()
            self.totalsecs = self.df.readint()
            self.totalturns = self.df.readint()
            self.totaldays = self.df.readint()
            self.coloration = self.df.readint()
            for i in range(12):
                self.options.append(self.df.readuchar())
            for i in range(255):
                self.narratives.append(self.df.readuchar())
            for i in range(200):
                self.quests.append(self.df.readint())
            for i in range(69):
                self.npcs.append(self.df.readuchar())
            self.quicktravel = self.df.readint()
            self.combatmode = self.df.readint()
            self.rules = self.df.readint()
            self.seed = self.df.readint()
            self.challenges = self.df.readint()
            for i in range(8):
                self.stats.append(self.df.readuchar())
            self.weather_type = self.df.readint()
            self.weather_duration = self.df.readint()
            self.weather_start = self.df.readint()
            self.weather_next = self.df.readint()
            self.cloud_darkener = self.df.readint()
            self.cloud_alpha = self.df.readfloat()
            self.weather_number = self.df.readint()
            self.weather_active = self.df.readint()
            for i in range(6):
                self.unknowns.append(self.df.readint())

            # Close the file
            self.df.close()

        except (IOError, struct.error), e:
            raise LoadException(str(e))

    def _sub_replicate(self, newsn):
        """
        Replicate our Book 2 specific data
        """
        newsn.combatmode = self.combatmode
        newsn.rules = self.rules
        newsn.seed = self.seed
        newsn.challenges = self.challenges
        newsn.weather_type = self.weather_type
        newsn.weather_duration = self.weather_duration
        newsn.weather_start = self.weather_start
        newsn.weather_next = self.weather_next
        newsn.cloud_darkener = self.cloud_darkener
        newsn.cloud_alpha = self.cloud_alpha
        newsn.weather_number = self.weather_number
        newsn.weather_active = self.weather_active

        for val in self.stats:
            newsn.stats.append(val)

class B3Savename(B2Savename):
    """
    Book 3 Character definitions
    """

    book = 3

    def __init__(self, df):
        super(B3Savename, self).__init__(df)

        # Book 3 specific vars
        self.savever = ''
        self.modpath = ''

    def read(self):
        """ Read in the whole save file from a file descriptor. """

        try:
            # Open the file
            self.df.open_r()

            # Based on BW's spec from
            # http://www.basiliskgames.com/forums/viewtopic.php?f=33&t=9328&start=60#p58108
            #
            # We evidently screwed something up, though, since we're off by
            # 24 bytes at the end. Almost certainly has bugs
            self.savename = self.df.readstr()
            self.savedate = self.df.readstr()
            self.savetime = self.df.readstr()
            self.savever = self.df.readstr()
            self.mapname = self.df.readstr()
            self.totalsecs = self.df.readint()
            self.totalturns = self.df.readint()
            self.totaldays = self.df.readint()
            self.coloration = self.df.readint()
            for i in range(12):
                self.options.append(self.df.readuchar())
            for i in range(255):
                self.narratives.append(self.df.readuchar())
            for i in range(300):
                self.quests.append(self.df.readint())
            for i in range(100):
                self.npcs.append(self.df.readuchar())
            self.quicktravel = self.df.readint()
            self.combatmode = self.df.readint()
            self.rules = self.df.readint()
            self.seed = self.df.readint()
            self.challenges = self.df.readint()
            for i in range(8):
                self.stats.append(self.df.readuchar())
            self.weather_type = self.df.readint()
            self.weather_duration = self.df.readint()
            self.weather_start = self.df.readint()
            self.weather_next = self.df.readint()
            self.cloud_darkener = self.df.readint()
            self.cloud_alpha = self.df.readfloat()
            self.weather_number = self.df.readint()
            self.weather_active = self.df.readint()
            # This is bogus - I'm sure we've lost 24 bytes somewhere
            # along the way
            for i in range(6):
                self.unknowns.append(self.df.readint())
            try:
                self.modpath = self.df.readstr()
            except LoadException:
                self.modpath = ''

            # Close the file
            self.df.close()

        except (IOError, struct.error), e:
            raise LoadException(str(e))

    def _sub_replicate(self, newsn):
        """
        Replicate our Book 3 specific data
        """
        newsn.savever = self.savever
        newsn.modpath = self.modpath
