#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2017 CJ Kucera, Elliot Kendall, Eitan Adler
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
import os
from io import BytesIO
from struct import pack, unpack

LOG = logging.getLogger(__name__)


class LoadException(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class FirstItemLoadException(LoadException):
    pass


class Savefile(object):
    """ Class that wraps around a file object, to simplify things """

    def __init__(self, filename=None, stringdata=None):
        """
        Empty object.  If only "filename" is passed, we will read
        from the filesystem.  If "stringdata" is also passed, we
        will use a BytesIO object instead.
        """

        if bool(filename is None) == bool(stringdata is None):
            raise LoadException('Must include filename xor stringdata')

        self.filename = filename
        self.stringdata = stringdata

        self.df = None
        self.opened_r = False
        self.opened_w = False

    def set_filename(self, filename) -> None:
        """
        Sets our filename (and clears our stringdata, if it's set)
        """
        self.filename = filename
        self.stringdata = None

    def is_stringdata(self) -> bool:
        """
        Returns True if we're a string-backed Savefile, false otherwise.
        """
        if self.stringdata is None:
            return False
        else:
            return True

    def exists(self) -> bool:
        """ Returns true if the file currently exists. """
        if self.is_stringdata():
            return True
        else:
            return os.path.exists(self.filename)

    def close(self) -> None:
        """ Closes the filehandle. """
        if self.opened_r or self.opened_w:
            self.df.close()
            self.opened_r = False
            self.opened_w = False

    def _open_mode(self, mode) -> None:
        if self.opened_r or self.opened_w:
            raise IOError('File is already open')
        if self.is_stringdata():
            self.df = BytesIO(self.stringdata)
        else:
            self.df = open(self.filename, mode)
        self.df.seek(0)

    def open_r(self) -> None:
        """ Opens a file for reading.  Throws IOError if unavailable"""
        self._open_mode('rb')
        self.opened_r = True

    def open_w(self) -> None:
        """ Opens a file for writing.  Throws IOError if unavailable"""
        self._open_mode('wb+')
        self.opened_w = True

    def eof(self) -> bool:
        """ Test to see if we're at EOF, since Python doesn't provide that for us. """
        # Note that theoretically there's some cases where a file error masquerades as
        # an EOF because of this code.  I can cope with that.
        a = self.df.read(1)
        if len(a) == 0:
            return True
        else:
            self.df.seek(-1, 1)
            return False

    def seek(self, offset, whence=0) -> int:
        """ Passthrough to the internal object. """
        return self.df.seek(offset, whence)

    def tell(self) -> int:
        """ Passthrough to the internal object. """
        return self.df.tell()

    def read(self, len=-1) -> int:
        """ Read the rest of the file from the handle. """
        return self.df.read(len)

    def readuchar(self) -> int:
        """ Read an unsigned character (1-byte) "integer" from the savefile. """
        if not self.opened_r:
            raise IOError('File is not open for reading')
        r = self.df.read(1)
        return unpack('B', r)[0]

    def writeuchar(self, charval) -> None:
        """ Write an unsigned character (1-byte) "integer" to the savefile. """
        if not self.opened_w:
            raise IOError('File is not open for writing')
        self.df.write(pack('B', charval))

    def readshort(self) -> int:
        """ Read a short (2-byte) integer from the savefile. """
        if not self.opened_r:
            raise IOError('File is not open for reading')
        return unpack('<H', self.df.read(2))[0]

    def writeshort(self, shortval) -> None:
        """ Write a short (2-byte) integer to the savefile. """
        if not self.opened_w:
            raise IOError('File is not open for writing')
        self.df.write(pack('<H', shortval))

    def readint(self) -> int:
        """ Read an integer from the savefile. """
        if not self.opened_r:
            raise IOError('File is not open for reading')
        return unpack('<I', self.df.read(4))[0]

    def writeint(self, intval) -> None:
        """ Write an integer to the savefile. """
        if not self.opened_w:
            raise IOError('File is not open for writing')
        self.df.write(pack('<I', intval))

    def readsint(self) -> int:
        """ Read a signed integer from the savefile. """
        if not self.opened_r:
            raise IOError('File is not open for reading')
        return unpack('<i', self.df.read(4))[0]

    def writesint(self, intval) -> None:
        """ Write a signed integer to the savefile. """
        if not self.opened_w:
            raise IOError('File is not open for writing')
        self.df.write(pack('<i', intval))

    def readfloat(self) -> float:
        """ Read a float from the savefile. """
        if not self.opened_r:
            raise IOError('File is not open for reading')
        return unpack('f', self.df.read(4))[0]

    def writefloat(self, floatval) -> None:
        """ Write a float to the savefile. """
        if not self.opened_w:
            raise IOError('File is not open for writing')
        self.df.write(pack('f', floatval))

    def readdouble(self) -> float:
        """ Read a double from the savefile. """
        if not self.opened_r:
            raise IOError('File is not open for reading')
        return unpack('d', self.df.read(8))[0]

    def writedouble(self, doubleval) -> None:
        """ Write a double to the savefile. """
        if not self.opened_w:
            raise IOError('File is not open for writing')
        self.df.write(pack('d', doubleval))

    def readstr(self) -> bytes:
        """ Read a string from the savefile, delimited by \r\n """
        if not self.opened_r:
            raise IOError('File is not open for reading')
        mystr = b''
        strpart = self.df.read(1)
        while len(strpart) == 1:
            mystr = mystr + strpart
            if mystr[-2:] == b"\r\n":
                return mystr[:-2]
            strpart = self.df.read(1)
        raise LoadException('Error reading string value |' +
                            strpart.decode('ascii') + '|')

    def writestr(self, strval) -> None:
        """ Write a string (delimited by \r\n) to the savefile. """
        if not self.opened_w:
            raise IOError('File is not open for writing')
        self.df.write(strval + b"\r\n")
