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

from eschalonb1.item import Item

class Unknowns:
    """ A class to hold some unknown data, so as not to muddy up the
        main Character class. """

    def __init__(self):
        """ A fresh object with no data. """

        self.initzero = -1
        self.charstring = ''
        self.charone = -1
        self.beginzero1 = -1
        self.beginzero2 = -1
        self.sparseiblock = []
        self.iblock1 = []
        self.ssiblocks1 = []
        self.ssiblocks2 = []
        self.ssiblocki = []
        self.extstr1 = ''
        self.extstr2 = ''
        self.anotherzero = -1
        self.anotherint = -1
        self.shortval = -1
        self.emptystr = ''
        self.iblock2 = [] # These are weird
        self.preinvs1 = ''
        self.preinvs2 = ''
        self.preinvzero1 = -1
        self.preinvzero2 = -1
        self.extradata = ''

    def replicate(self):
        newunknown = Unknowns()

        # Simple Values
        newunknown.initzero = self.initzero
        newunknown.charstring = self.charstring
        newunknown.charone = self.charone
        newunknown.beginzero1 = self.beginzero1
        newunknown.beginzero2 = self.beginzero2
        newunknown.extstr1 = self.extstr1
        newunknown.extstr2 = self.extstr2
        newunknown.anotherzero = self.anotherzero
        newunknown.anotherint = self.anotherint
        newunknown.shortval = self.shortval
        newunknown.emptystr = self.emptystr
        newunknown.preinvs1 = self.preinvs1
        newunknown.preinvs2 = self.preinvs2
        newunknown.preinvzero1 = self.preinvzero1
        newunknown.preinvzero2 = self.preinvzero2
        newunknown.extradata = self.extradata

        # Arrays
        for val in self.sparseiblock:
            newunknown.sparseiblock.append(val)
        for val in self.iblock1:
            newunknown.iblock1.append(val)
        for val in self.ssiblocks1:
            newunknown.ssiblocks1.append(val)
        for val in self.ssiblocks2:
            newunknown.ssiblocks2.append(val)
        for val in self.ssiblocki:
            newunknown.ssiblocki.append(val)
        for val in self.iblock2:
            newunknown.iblock2.append(val)

        # ... aaand return our new object
        return newunknown

    def iblock(self, num, arr, desc='Block of integers'):
        """ Display a block of unknown integers. """
        print "%s %d:" % (desc, num)
        for i in arr:
            print "\t0x%08X - %d" % (i, i)

    def display(self):
        """ Show a textual description of all unknown fields. """

        print "Initial Zero: %d" % self.initzero
        print "Empty Character String: %s" % self.charstring
        print "Usually 1: %d" % self.charone
        print "Another integer 1, generally 0: %d" % self.beginzero1
        print "Another integer 2, generally 0: %d" % self.beginzero2
        self.iblock(1, self.sparseiblock, 'Sparse integers (interleaved with char statuses)')
        self.iblock(1, self.iblock1)
        print "Block of 2 Strings plus 1 Integer:"
        for i in range(len(self.ssiblocks1)):
            print "\tBlock %d:" % (i+1)
            print "\t\tString 1: %s" % self.ssiblocks1[i]
            print "\t\tString 2: %s" % self.ssiblocks1[i]
            print "\t\tInt: %d" % self.ssiblocki[i]
        print "Extra string 1: %s" % self.extstr1
        print "Extra string 2: %s" % self.extstr2
        print "Another zero: %d" % self.anotherzero
        print "Another int (generally a multiple of 256): %d" % self.anotherint
        print "A short int: %d" % self.shortval
        print "A string (always blank for me): %s" % self.emptystr
        self.iblock(2, self.iblock2)
        print "Pre-inventory blank string 1: %s" % self.preinvs1
        print "Pre-inventory blank string 2: %s" % self.preinvs2
        print "Pre-inventory zero 1: %d" % self.preinvzero1
        print "Pre-inventory zero 2: %d" % self.preinvzero2
        if (len(self.extradata) != 0):
            print "File has extra data appended at the end: %d bytes" % len(self.extradata)
