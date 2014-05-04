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
import csv
import glob
import base64
import cStringIO
from eschalon import constants as c
from eschalon.savefile import LoadException

class GoldRanges(object):
    """
    Class to hold information about the gold ranges seen in general_items.csv.
    Used primarily to attempt to normalize item names during savegame -> global
    conversions.  The Book III Gold items are nice enough to have their ranges
    in the name of the item, whereas Book II just has labels.  We do some munging
    to pretend that everything's in the Book III format.

    Note that the Book III values haven't actually been experimentally verified.
    """
    def __init__(self):
        """
        Initialize our empty fields.  "exact" is a dict used to match an
        exact amount of gold, of which a couple are valid.  "ranges" defines
        the ranges we know about, and "labels" are the labels which are
        associated with those ranges.
        """
        self.exact = {}
        self.ranges = []
        self.labels = []
        self.max_seen = -1

    def add_item(self, item_name):
        """
        Adds a gold range to ourselves, based on interpreting an item name.
        """
        parts = item_name.split()
        if len(parts) == 3:
            if parts[1] == 'Gold' and parts[2][:5] == 'Piece':
                self.exact[int(parts[0])] = True
                if int(parts[0]) > self.max_seen:
                    self.max_seen = int(parts[0])
            elif parts[2][0] == '(' and parts[2][-1] == ')':
                item_ranges = parts[2][1:-1].split('-')
                if len(item_ranges) == 2:
                    self.ranges.append((int(item_ranges[0]), int(item_ranges[1])))
                    self.labels.append(parts[0])
                    if int(item_ranges[1]) > self.max_seen:
                        self.max_seen = int(item_ranges[1])
        elif c.book == 2 and len(parts) == 2 and parts[1] == 'Gold':
            # The ranges I observed experimentally turned out to be:
            #   Small: 16-35
            #   Medium: 76-125
            #   Large: 151-250
            # I've widened those ranges a little bit here
            if parts[0] == 'Small':
                self.add_item('Small Gold (1-74)')
            elif parts[0] == 'Medium':
                self.add_item('Medium Gold (75-149)')
            else:
                self.add_item('Large Gold (150-250)')

    def get_equivalent(self, item_name):
        """
        Returns our best guess about a valid global item name for the given
        item name.
        """
        if self.max_seen >= 0 and 'Gold Piece' in item_name:
            parts = item_name.split()
            if len(parts) == 3:
                if parts[1] == 'Gold' and parts[2][:5] == 'Piece':
                    num_gold = int(parts[0])
                    if num_gold in self.exact:
                        # We're already a known specific gold value
                        return item_name

                    for (label, (begin, end)) in zip(self.labels, self.ranges):
                        if num_gold >= begin and num_gold <= end:
                            # We found ourselves in a range we know about
                            if c.book == 3:
                                return '%s Gold (%d-%d)' % (label, begin, end)
                            else:
                                return '%s Gold' % (label)

                    # If we got here, we didn't have an exact number and also
                    # don't have a valid range.  Just re-run with our max
                    # known value, on the assumption that our range extends
                    # as low as it can.
                    return self.get_equivalent('%d Gold Pieces' % (self.max_seen))

        # Default, just return our passed-in name
        return item_name

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

        # Cache of our known item list, so that we only read it once.
        self.itemlist = None
        self.itemdict = None
        self.goldranges = None
        self.material_items = None

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

    def get_filehandle(self, filename, directory='gfx'):
        """
        Reads a given filename from our dir and returns a filehandle-like object to
        its data, using the cStringIO object.  Consequently, the returned filehandle
        will be read-only.  Calls self.readfile() to do most of our work.
        """
        return cStringIO.StringIO(self.readfile(filename, directory))

    def populate_datapak_info(self):
        """
        Populates some internal structures based on information found in
        Eschalon's datapak:
            1) Valid item names from the main general_items.csv
            2) Gold range information from general_items.csv (needed to
               tarnslate savegame gold values back to global values)
            3) Savegame Weapon/Armor names which can be mapped back to
               base global item names.
        """
        self.itemlist = []
        self.itemdict = {}
        self.goldranges = GoldRanges()
        self.material_items = {}
        try:
            df = self.get_filehandle('general_items.csv', 'data')
            reader = csv.DictReader(df)
            for row in reader:
                if row['DESCRIPTION'] != '':
                    self.itemdict[row['DESCRIPTION']] = True

                if row['Item Category'] == 'IC_GOLD':
                    self.goldranges.add_item(row['DESCRIPTION'])

                materialid = int(row['Material'])
                if materialid == 1:
                    for material in c.materials_wood:
                        self.material_items['%s %s' % (material, row['DESCRIPTION'])] = row['DESCRIPTION']
                elif materialid == 2:
                    for material in c.materials_metal:
                        self.material_items['%s %s' % (material, row['DESCRIPTION'])] = row['DESCRIPTION']
                elif materialid == 3:
                    for material in c.materials_fabric:
                        self.material_items['%s %s' % (material, row['DESCRIPTION'])] = row['DESCRIPTION']
            df.close()
        except:
            pass

        self.itemlist = sorted(self.itemdict.keys())

    def get_itemlist(self):
        """
        Returns a list of valid item names from the main general_items.csv
        """
        if self.itemlist is None:
            self.populate_datapak_info()
        return self.itemlist

    def get_itemdict(self):
        """
        Returns a dictionary of valid item names from the main general_items.csv
        Nearly the same thing as get_itemlist, but more useful if you're comparing
        another list of items versus this
        """
        if self.itemdict is None:
            self.populate_datapak_info()
        return self.itemdict

    def get_global_name(self, item_name):
        """
        Returns an attempt to normalize our given item_name into a value
        appropriate for global map files.
        """
        if self.goldranges is None:
            self.populate_datapak_info()

        if 'Gold Piece' in item_name:
            if self.goldranges:
                return self.goldranges.get_equivalent(item_name)
        elif item_name[:10] == 'Scroll of ':
            return item_name[10:]
        else:
            for (key, val) in self.material_items.items():
                if key in item_name:
                    return val
            return item_name

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

    def populate_datapak_info(self):
        """
        Compatibility function, does nothing
        """
        pass

    def get_itemlist(self):
        """
        Returns an empty list.  It might be nice to come up with a static list
        to put in here, instead
        """
        return []

    def get_itemdict(self):
        """
        Returns an empty dict.  It might be nice to come up with a static list
        to put in here, instead
        """
        return {}

    def get_global_name(self, item_name):
        """
        Theoretically returns a normalized "global" map item name, but in reality
        just returns the passed-in name.
        """
        return item_name
