#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2012 CJ Kucera
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

import sys
from eschalon.map import Map
from eschalon.savefile import LoadException

class MapCLI(object):

    def __init__(self, options, prefs):
        """ A fresh object, with no data. """
        self.options = options
        self.prefs = prefs

    def run(self):
        
        options = self.options

        # Load in our file
        try:
            map = Map(options['filename'])
            map.read()
            self.map = map
        except LoadException, e:
            print '"' + options['filename'] + '" could not be opened'
            print e
            return False

        # The --list options will return automatically.  Everything
        # else will trigger a write once everything's done
        if (options['list']):
            return self.display(options['listoptions'], options['unknowns'])
        
        # If we've gotten here, write the file
        #char.write()
        
        # ... and return
        return True

    def display_header(self):
        """ Print out a textual representation of the base map info."""

        map = self.map
        print "Map %s (%s)" % (map.mapid, map.mapname)
        print "Soundfiles: %s, %s, %s" % (map.soundfile1, map.soundfile2, map.soundfile3)
        print "Skybox: %s" % (map.skybox)
        print "Skybox Parallax 1: %d" % (map.parallax_1)
        print "Skybox Parallax 2: %d" % (map.parallax_2)
        print "Cloud Overlay: %d" % (map.clouds)
        print "North Exit: %s" % (map.exit_north)
        print "East Exit: %s" % (map.exit_east)
        print "South Exit: %s" % (map.exit_south)
        print "West Exit: %s" % (map.exit_west)
        print "RGBA: %d/%d/%d/%d" % (map.color_r, map.color_g, map.color_b, map.color_a)
        if (map.is_savegame()):
            print "(This is a savegame map file)"
        elif (map.is_global()):
            print "(This is a global map file)"
        else:
            print "Savegame IDs: %d, %d, %d" % (map.savegame_1, map.savegame_2, map.savegame_3)
        print

    def display_squares(self, unknowns=False):
        """ Print out a textual representation of the map's squares."""
        map = self.map
        for y in range(len(map.squares)):
            print 'Row %d:' % y
            print
            for x in range(len(map.squares[y])):
                if (map.squares[y][x].hasdata() != 0):
                    print ' * Cell %d:' % x
                    print map.squares[y][x].display(unknowns)
                    print 
        pass

    def display_scripts(self, unknowns=False):
        """ Print out a textual representation of the map's scripts."""
        i = 0
        for script in self.map.scripts:
            i = i + 1
            print 'Object Number %d' % i
            print script.display(unknowns)
            print

    def display_txtmap(self):
        """ Print out a little ascii map. """
        map = self.map
        i = 0
        for row in map.squares:
            i = i +1
            if (i % 2 == 0):
                sys.stdout.write(' ')
            for square in row:
                if (square.wall > 0):
                    sys.stdout.write('* ')
                else:
                    sys.stdout.write('  ')
            print
        print

    def display_unknowns(self):
        """ Show our unknown values. """
        map = self.map

        print "UNKNOWNS"
        print "--------"
        print
        print "Unknown integer 1: %d" % (map.unknowni1)
        print "Unknown short 1: %d" % (map.unknownh1)
        print

    def display(self, listoptions, unknowns=False):
        """ Print out a textual representation of the map."""

        self.display_header()

        if (listoptions['squares']):
            self.display_squares(unknowns)

        if (listoptions['objects']):
            self.display_scripts(unknowns)

        if (listoptions['txtmap']):
            print "Note: you need a really small font and a rather large console"
            print "for this to make any sense."
            self.display_txtmap()
            print "Note: you need a really small font and a rather large console"
            print "for this to make any sense."

        if (unknowns):
            self.display_unknowns()
