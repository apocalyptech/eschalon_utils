#!/usr/bin/env python
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

try:
    import czipfile as zipfile
    fast_zipfile = True
except ImportError:
    import eschalon.fzipfile as zipfile
    fast_zipfile = False

try:
    from Crypto.Cipher import AES
    have_aes = True
except ImportError:
    have_aes = False

import os
import glob
import base64
from eschalon import constants as c
from eschalon.savefile import LoadException

class Datapak(object):
    """
    Class to handle the encrypted datapak file used in Books 2 and 3.

    I'm fully aware that all this munging about is merely obfuscation and
    wouldn't actually prevent anyone from getting to the data, but I feel
    obligated to go through the motions regardless.  Hi there!  Note that I 
    *did* get BW's permission to access the graphics data this way.
    """

    def __init__(self, filename):
        self.filename = filename

        if not os.path.isfile(filename):
            raise LoadException('Datapak %s is not found' % (filename))

        s = base64.urlsafe_b64decode(c.s)
        d = base64.urlsafe_b64decode(c.d)
        iv = d[:16]
        self.aesenc = d[16:]
        self.aes = AES.new(s, AES.MODE_CBC, iv)

        plain = self.aes.decrypt(self.aesenc)
        pad = ord(plain[-1])
        text = plain[:-pad]

        self.zipobj = zipfile.ZipFile(filename, 'r')
        self.zipobj.setpassword(text)

    def readfile(self, filename, directory='gfx'):
        """
        Reads a given filename from the given dir.  Can raise a LoadException
        if the file is not found
        """
        filename = '%s/%s' % (directory, filename)
        try:
            return self.zipobj.read(filename)
        except KeyError:
            raise LoadException('Filename %s not found in datapak' % (filename))

    def filelist(self):
        """
        Returns a list of all files inside the datapak.
        """
        return self.zipobj.namelist()

class EschalonData(object):
    """
    Class to load data from Eschalon's data directory.  This actually only
    supports books 2 and 3, because there's not much point in abstracting
    what's available in Book 1.  This will typically read from inside the
    game's encrypted "datapak" using the Datapak class, but some versions
    of Book 3 on OSX are bundled such that the contents are on the
    filesystem directly.  Presumably once the mod support gets expanded,
    this class might end up doing a bit more than it does now.
    """

    DATA_DIRS = [ 'data', 'gfx', 'maps', 'music', 'sound' ]

    def __init__(self, gamedir):
        """
        Constructor.  "gamedir" should be the base game directory, whether
        it contains a datapak or a filesystem structure.
        """

        # First read a couple of variables from our global environment
        self.fast_zipfile = fast_zipfile
        self.have_aes = have_aes

        # Our datapak object.  If this remains None, it means that we're
        # reading from the filesystem structure instead.
        self.datapak = None

        # Set our base gamedir.  This also does the work of actually
        # finding out where our data is.
        self.set_gamedir(gamedir)

    def set_gamedir(self, gamedir):
        """
        Used to update our game directory - this might happen as the
        result of a preferences update, for instance.  This will
        actually look for the bare directories first (right now this
        will only be found "in the wild" in Book 3 v1.021 on OSX),
        but that'll allow us to more easily selectively enforce our
        pycrypto dependency (and should make for some easier mod
        testing, while support in the Book 3 engine is still
        forthcoming).  If the necessary directories aren't found,
        we'll look for the datapak as usual, and complain if we can't
        use the AES module.

        This can raise a LoadException if our necessary data isn't
        found.
        """
        self.gamedir = gamedir

        if not os.path.isdir(self.gamedir):
            raise LoadException('"%s" is not a valid directory' % (self.gamedir))

        # Check to see if we have a local Eschalon data structure
        found_dirs = True
        for check_dir in self.DATA_DIRS:
            if not os.path.isdir(os.path.join(self.gamedir, check_dir)):
                found_dirs = False

        if found_dirs:
            # We're using local directories
            self.datapak = None
        else:
            # We'll try loading the datapak
            datapak_file = os.path.join(self.gamedir, 'datapak')
            if os.path.isfile(datapak_file):
                if self.have_aes:
                    # If we get here, set up a datapak object.  This could, itself,
                    # raise an Exception under some circumstances
                    self.datapak = Datapak(datapak_file)
                else:
                    raise LoadException('Book 2/3 Graphics requires pycrypto, please install it:'
                        "\n\n\t"
                        'http://www.dlitz.net/software/pycrypto/'
                        "\n\n"
                        'For most Linux distributions, the package name is "python-crypto"')
            else:
                raise LoadException('Could not find datapak or gfx directory!')

    def filelist(self):
        """
        Returns a list of all files available to us
        """
        if self.datapak is None:
            namelist = []
            for directory in self.DATA_DIRS:
                namelist = namelist + glob.glob(os.path.join(self.gamedir, directory, '*'))
            retlist = []
            for filename in namelist:
                retlist.append(os.path.relpath(filename, self.gamedir))
            return retlist
        else:
            return self.datapak.filelist()

    def readfile(self, filename, directory='gfx'):
        """
        Reads a given filename from the given dir.  The directory defaults to 'gfx' if
        not specified, since historically the majority of files we intend to open are
        in the gfx directory.  Returns the data of the file requested, not a file-like
        object.
        
        This can raise a LoadException if the file is not found, or if other errors
        occur.
        """
        if self.datapak is None:
            to_open = os.path.join(self.gamedir, directory, filename)
            if os.path.isfile(to_open):
                try:
                    with open(to_open, 'r') as df:
                        return df.read()
                except IOError, e:
                    raise LoadException('Filename %s could not be opened: %s' % (to_open, e))
            else:
                raise LoadException('Filename %s could not be found' % (to_open))
        else:
            return self.datapak.readfile(filename, directory)

    @staticmethod
    def new(book, gamedir):
        """
        Returns a new object of the appropriate type.  For Books 2+3, we'll
        just instantiate ourselves.  For Book 1, we'll use a compatibility
        object.
        """
        if book == 1:
            return B1EschalonData(gamedir)
        else:
            return EschalonData(gamedir)

class B1EschalonData(object):
    """
    Class to mimic functionality of EschalonData for Book 1.  This is
    primarily so that the main Gfx object can be agnostic about what
    kinds of objects it's passed, without having to add complexity to
    the main EschalonData class.
    """

    def __init__(self, gamedir):
        """
        Initialization - just store our gamedir, primarily.
        """
        self.set_gamedir(gamedir)

    def set_gamedir(self, gamedir):
        """
        Sets our gamedir.  Can throw a LoadException if it doesn't
        exist.
        """
        self.gamedir = gamedir

        if not os.path.isdir(self.gamedir):
            raise LoadException('"%s" is not a valid directory' % (self.gamedir))

    def filelist(self):
        """
        Returns a list of all files available to us.  Not actually useful for Book 1,
        really, but we'll implement it just in case.
        """
        namelist = []
        for (dirpath, dirnames, filenames) in os.walk(self.gamedir):
            for filename in filenames:
                namelist.append(os.path.relpath(os.path.join(dirpath, filename), self.gamedir))
        return namelist

    def readfile(self, filename, directory=''):
        """
        Returns the contents of the specified file.  Book 2 has no "gfx" directory like in
        Books 2 and 3, so the default here is to load the file from the base dir itself.
        """
        with open(os.path.join(self.gamedir, directory, filename)) as df:
            return df.read()
