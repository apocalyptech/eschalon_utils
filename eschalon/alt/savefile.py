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

#
# This was my first test of seeing if I could speed up file loading times by
# loading the entire file into memory all at once and then referencing the
# data in memory, instead of doing a whole bunch of read() calls to the file
# descriptor.  It seems as though doing so, at least in this incarnation, is
# rather slower, though, by a good half second or so (which is maybe a 40%
# increase in time, so that's not insignificant).  Denormalizing some of these
# function calls let me get the difference down to about a quarter of a second,
# and I didn't feel like taking the time to see if there were any other corners
# I could cut.  Doubtless some of the speed decrease was due to me adding in
# some other things here (the FirstLoad check, etc), but in the end I figured I'd
# just abandon the idea for now.
#

from struct import pack, unpack

class LoadException(Exception):

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return repr(self.text)

class FirstItemLoadException(LoadException):
    pass

class Savefile:
    """ Class that wraps around a file object, to simplify things """

    def __init__(self, filename):
        """ Empty object. """
        self.filename = filename
        self.df = None
        self.opened_r = False
        self.opened_w = False
        self.data = ''
        self.curidx = -1
        self.filesize = -1

    def close(self):
        """ Closes the filehandle. """
        if (self.opened_r or self.opened_w):
            if (self.opened_w):
                # When reading, we close the handle right away
                self.df.close()
            self.opened_r = False
            self.opened_w = False

    def open_r(self):
        """ Opens a file for reading.  Throws IOError if unavailable"""
        if (self.opened_r or self.opened_w):
            raise IOError('File is already open')
        self.df = open(self.filename, 'rb')
        self.data = self.df.read()
        self.curidx = 0
        self.df.close()
        self.filesize = len(self.data)
        self.opened_r = True

    def open_w(self):
        """ Opens a file for writing.  Throws IOError if unavailable"""
        if (self.opened_r or self.opened_w):
            raise IOError('File is already open')
        self.df = open(self.filename, 'wb')
        self.df.seek(0)
        self.opened_w = True

    def eof(self):
        """ Check to see if we're at EOF. """
        return (self.curidx == self.filesize)

    def readcheck(self, first=False):
        """ Some basic checks before we do a read. """
        if (not self.opened_r):
            raise IOError('File is not open for reading')
        if (self.eof()):
            if (first):
                raise FirstItemLoadException('At EOF')
            else:
                raise LoadException('At EOF')

    def read(self, len=None, first=False):
        """ Read the from our virtual filehandle. """
        self.readcheck(first)
        if (len is None):
            len = self.filesize - self.curidx
        if (self.curidx + len > self.filesize):
            raise LoadException('Not enough data in file')
        self.curidx = self.curidx + len
        return self.data[self.curidx - len:self.curidx]

    def readchar(self, first=False):
        """ Read a signed character (1-byte) "integer" from the savefile. """
        return unpack('b', self.read(1, first))[0]

    def writechar(self, charval):
        """ Write a signed character (1-byte) "integer" to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('b', charval))

    def readuchar(self, first=False):
        """ Read an unsigned character (1-byte) "integer" from the savefile. """
        return unpack('B', self.read(1, first))[0]

    def writeuchar(self, charval):
        """ Write an unsigned character (1-byte) "integer" to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('B', charval))

    def readshort(self, first=False):
        """ Read a short (2-byte) integer from the savefile. """
        return unpack('<H', self.read(2, first))[0]

    def writeshort(self, shortval):
        """ Write a short (2-byte) integer to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('<H', shortval))

    def readint(self, first=False):
        """ Read an integer from the savefile. """
        return unpack('<I', self.read(4, first))[0]

    def writeint(self, intval):
        """ Write an integer to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('<I', intval))

    def readfloat(self, first=False):
        """ Read a float (actually a double) from the savefile. """
        return unpack('d', self.read(8, false))[0]

    def writefloat(self, floatval):
        """ Write a float (actually a double) to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('d', floatval))

    def readstr(self, first=False):
        """ Read a string from the savefile, delimited by \r\n """
        self.readcheck(first)
        pos = self.data.find("\r\n", self.curidx)
        if (pos == -1):
            raise LoadException('Error reading string value')
        else:
            len = pos - self.curidx + 2
            self.curidx = self.curidx + len
            return self.data[self.curidx-len:self.curidx-2]

    def writestr(self, strval):
        """ Write a string (delimited by \r\n) to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(strval + "\r\n")
