#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Character Editor
# Copyright (C) 2008 CJ Kucera
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
from eschalonb1.map import Map
from eschalonb1.loadexception import LoadException

class MapCLI:

    def __init__(self, options):
        """ A fresh object, with no data. """
        self.options = options

    def run(self):
        
        options = self.options

        # Load in our file
        try:
            map = Map(options['filename'])
            map.read()
            self.map = map
        except LoadException, e:
            print '"' + options['filename'] + '" could not be opened'
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
        print "Soundfiles: %s, %s" % (map.soundfile1, map.soundfile2)
        print "Skybox: %s" % (map.skybox)
        print "RGBA: %d/%d/%d/%d" % (map.color_r, map.color_g, map.color_b, map.color_a)
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
                    map.squares[y][x].display(unknowns)
                    print 
        pass

    def display_scripts(self, unknowns=False):
        """ Print out a textual representation of the map's scripts."""
        pass

    def display_txtmap(self):
        """ Print out a little ascii map. """
        map = self.map
        i = 0
        for row in map.squares:
            i = i +1
            if (i % 2 == 0):
                sys.stdout.write(' ')
            for square in row:
                if square.wall:
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
        print "Unknown string 1: %s" % (map.unknowns1)
        print "Unknown string 2: %s" % (map.unknowns2)
        print "Unknown string 3: %s" % (map.unknowns3)
        print "Unknown string 4: %s" % (map.unknowns4)
        print "Unknown string 5: %s" % (map.unknowns5)
        print
        print "Unknown integer 1: %d" % (map.unknowni1)
        print "Unknown integer 2: %d" % (map.unknowni2)
        print "Unknown integer 3: %d" % (map.unknowni3)
        print "Unknown integer 4: %d" % (map.unknowni4)
        print "Unknown integer 5: %d" % (map.unknowni5)
        print "Unknown integer 6: %d" % (map.unknowni6)
        print "Unknown integer 7: %d" % (map.unknowni7)
        print
        print "Unknown short 1: %d" % (map.unknownh1)
        print

    def display(self, listoptions, unknowns=False):
        """ Print out a textual representation of the map."""

        self.display_header()

        if (listoptions['squares']):
            self.display_squares(unknowns)

        if (listoptions['scripts']):
            self.display_scripts(unknowns)

        if (listoptions['txtmap']):
            print "Note: you need a really small font for this to make any sense."
            self.display_txtmap()
            print "Note: you need a really small font for this to make any sense."

        if (unknowns):
            self.display_unknowns()
