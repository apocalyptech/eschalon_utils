#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
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

from struct import pack, unpack
from eschalonb1.loadexception import LoadException

class Savefile:
    """ Class that wraps around a file object, to simplify things """

    def __init__(self, filename):
        """ Empty object. """
        self.filename = filename
        self.df = None
        self.opened_r = False
        self.opened_w = False

    def close(self):
        """ Closes the filehandle. """
        if (self.opened_r or self.opened_w):
            self.df.close()
            self.opened_r = False
            self.opened_w = False

    def open_r(self):
        """ Opens a file for reading.  Throws IOError if unavailable"""
        if (self.opened_r or self.opened_w):
            raise IOError('File is already open')
        self.df = open(self.filename, 'rb')
        self.opened_r = True

    def open_w(self):
        """ Opens a file for writing.  Throws IOError if unavailable"""
        if (self.opened_r or self.opened_w):
            raise IOError('File is already open')
        self.df = open(self.filename, 'wb')
        self.df.seek(0)
        self.opened_w = True

    def read(self):
        """ Read the rest of the file from the handle. """
        return self.df.read()

    def readshort(self):
        """ Read a short (2-byte) integer from the savefile. """
        if (not self.opened_r):
            raise IOError('File is not open for reading')
        return unpack('<H', self.df.read(2))[0]

    def writeshort(self, shortval):
        """ Write a short (2-byte) integer to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('<H', shortval))

    def readint(self):
        """ Read an integer from the savefile. """
        if (not self.opened_r):
            raise IOError('File is not open for reading')
        return unpack('<I', self.df.read(4))[0]

    def writeint(self, intval):
        """ Write an integer to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('<I', intval))

    def readfloat(self):
        """ Read a float (actually a double) from the savefile. """
        if (not self.opened_r):
            raise IOError('File is not open for reading')
        return unpack('d', self.df.read(8))[0]

    def writefloat(self, floatval):
        """ Write a float (actually a double) to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(pack('d', floatval))

    def readstr(self):
        """ Read a string from the savefile, delimited by \r\n """
        if (not self.opened_r):
            raise IOError('File is not open for reading')
        mystr = ''
        strpart = self.df.read(1)
        while (len(strpart) == 1):
            mystr = mystr + strpart
            if (mystr[-2:] == "\r\n"):
                return mystr[:-2]
            strpart = self.df.read(1)
        # Shouldn't ever get to here
        raise LoadException('Error reading string value')

    def writestr(self, strval):
        """ Write a string (delimited by \r\n) to the savefile. """
        if (not self.opened_w):
            raise IOError('File is not open for writing')
        self.df.write(strval + "\r\n")
