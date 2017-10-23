#!/usr/bin/env python
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
import base64
import csv
import glob
import io
import logging
import os
import zipfile

from Crypto.Cipher import AES

from eschalon.constants import constants as c
from eschalon.savefile import LoadException

LOG = logging.getLogger(__name__)


fast_zipfile = True


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
                    self.ranges.append(
                        (int(item_ranges[0]), int(item_ranges[1])))
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
                        if begin <= num_gold <= end:
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


class EntHelper(object):
    """
    Class to store data about our entities.  Basically just a glorified
    dictionary.  Previously this had been stored inside the various
    Constants classes, but it never really belonged there.
    """

    def __init__(self, name, health, gfxfile, friendly, movement, dirs=8,
                 width=64, height=64, frames=17, entscript=''):
        """
        Constructor.  Note that for Book 1, only name, health, gfxfile, friendly,
        and movement will be specified.
        """
        self.name = name
        self.health = health
        self.gfxfile = gfxfile
        self.friendly = friendly
        self.movement = movement
        self.dirs = dirs
        self.width = width
        self.height = height
        self.frames = frames
        self.entscript = entscript


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
            raise LoadException(
                'Filename %s not found in datapak' % (filename))

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

    DATA_DIRS = ['data', 'gfx', 'maps', 'music', 'sound']

    empty_name = None
    random_name = None

    def __init__(self, gamedir, modpath=None):
        """
        Constructor.  "gamedir" should be the base game directory, whether
        it contains a datapak or a filesystem structure.
        """

        # Cache of our known item list, so that we only read it once.
        self.itemlist = None
        self.itemdict = None
        self.goldranges = None
        self.material_items = None

        # Entities
        self.entitytable = None

        # Our datapak object.  If this remains None, it means that we're
        # reading from the filesystem structure instead.
        self.datapak = None

        # Set our base gamedir.  This also does the work of actually
        # finding out where our data is.
        self.set_gamedir(gamedir)

        self.modpath = modpath

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
            raise LoadException(
                '"%s" is not a valid directory' % (self.gamedir))

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
                self.datapak = Datapak(datapak_file)
            else:
                raise LoadException('Could not find datapak or gfx directory!')

    def filelist(self):
        """
        Returns a list of all files available to us
        """
        if self.datapak is None:
            namelist = []
            for directory in self.DATA_DIRS:
                namelist = namelist + \
                    glob.glob(os.path.join(self.gamedir, directory, '*'))
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
                except IOError as e:
                    raise LoadException(
                        'Filename %s could not be opened: %s' % (to_open, e))
            else:
                raise LoadException(
                    'Filename %s could not be found' % (to_open))
        else:
            return self.datapak.readfile(filename, directory)

    def get_filehandle(self, filename, directory='gfx'):
        """
        Reads a given filename from our dir and returns a filehandle-like object to
        its data, using the cStringIO object.  Consequently, the returned filehandle
        will be read-only.  Calls self.readfile() to do most of our work.
        """
        return io.StringIO(self.readfile(filename, directory))

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
        self.entitytable = {}

        # First load in all available information from general_items.csv
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
                        self.material_items['%s %s' % (
                            material, row['DESCRIPTION'])] = row['DESCRIPTION']
                elif materialid == 2:
                    for material in c.materials_metal:
                        self.material_items['%s %s' % (
                            material, row['DESCRIPTION'])] = row['DESCRIPTION']
                elif materialid == 3:
                    for material in c.materials_fabric:
                        self.material_items['%s %s' % (
                            material, row['DESCRIPTION'])] = row['DESCRIPTION']
            df.close()
        except:
            pass

        # Add RANDOM/EMPTY to the list of valid names, if we actually
        # have data.
        if len(self.itemdict) > 0:
            if self.empty_name:
                self.itemdict[self.empty_name] = True
            if self.random_name:
                self.itemdict[self.random_name] = True

        # Populate a sorted itemlist object as well.
        self.itemlist = sorted(list(self.itemdict.keys()),
                               key=lambda s: s.lower())

        # Now try to load in all available entity information
        try:
            df = self.get_filehandle('entities.csv', 'data')
            self.read_entities(df)
            df.close()
        except:
            pass
        try:
            path = os.path.join(self.modpath, 'entities.csv')
            df = open(path, 'r')
            self.read_entities(df)
            df.close()
        except:
            pass

    def read_entities(self, df):
        reader = csv.DictReader(df)
        for row in reader:
            if row['file'].strip() == '':
                continue
            xoff = int(row['Xoff'])
            yoff = int(row['Yoff'])
            width = 64 + xoff
            height = 64 + yoff
            name = row['Name']
            if (int(row['Dirs']) == 1):
                name = '%s *' % (name)
            script = row['Script'].strip()
            if script == '*':
                script = ''
            # In the event of multiple IDs found in the file, Eschalon itself will favor
            # the first, so we should check for this.
            ent_id_int = int(row['ID'])
            if ent_id_int not in self.entitytable:
                self.entitytable[ent_id_int] = EntHelper(name=name,
                                                         health=int(row['HP']),
                                                         gfxfile='%s.png' % (
                                                             row['file']),
                                                         friendly=int(
                                                             row['Align']),
                                                         movement=int(
                                                             row['Move']),
                                                         dirs=int(row['Dirs']),
                                                         width=width,
                                                         height=height,
                                                         frames=int(
                                                             row['Frame']),
                                                         entscript=script)

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
            for (key, val) in list(self.material_items.items()):
                if key in item_name:
                    return val
            return item_name

    def get_entitytable(self):
        """
        Returns a dict of entities from the main entities.csv
        """
        if self.entitytable is None:
            self.populate_datapak_info()
        return self.entitytable

    def get_entity(self, entid):
        """
        Returns the requested entity, or None if not found
        """
        if self.entitytable is None:
            self.populate_datapak_info()

        try:
            return self.entitytable[entid]
        except KeyError:
            return None

    @staticmethod
    def new(book, gamedir, modpath=None):
        """
        Returns a new object of the appropriate type.  For Books 2+3, we'll
        just instantiate ourselves.  For Book 1, we'll use a compatibility
        object.
        """
        if book == 1:
            return B1EschalonData(gamedir, modpath)
        elif book == 2:
            return B2EschalonData(gamedir, modpath)
        else:
            return B3EschalonData(gamedir, modpath)


class B1EschalonData(object):
    """
    Class to mimic functionality of EschalonData for Book 1.  This is
    primarily so that the main Gfx object can be agnostic about what
    kinds of objects it's passed, without having to add complexity to
    the main EschalonData class.
    """

    def __init__(self, gamedir, modpath=None):
        """
        Initialization - just store our gamedir, primarily.
        """
        self.set_gamedir(gamedir)
        self.entitytable = None

    def set_gamedir(self, gamedir):
        """
        Sets our gamedir.  Can throw a LoadException if it doesn't
        exist.
        """
        self.gamedir = gamedir

        if not os.path.isdir(self.gamedir):
            raise LoadException(
                '"%s" is not a valid directory' % (self.gamedir))

    def filelist(self):
        """
        Returns a list of all files available to us.  Not actually useful for Book 1,
        really, but we'll implement it just in case.
        """
        namelist = []
        for (dirpath, dirnames, filenames) in os.walk(self.gamedir):
            for filename in filenames:
                namelist.append(os.path.relpath(
                    os.path.join(dirpath, filename), self.gamedir))
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
        Compatibility function.  Doesn't actually read any data from anywhere, but this
        will store information that we've hardcoded but are pretending to be reading.
        Right now that just means entities.
        """

        # Entities
        self.entitytable = {

            # Enemies
            0x01: EntHelper('Fanged Salamander', 9, 1, 0, 1),
            0x02: EntHelper('Bloodsipper', 17, 2, 0, 1),
            0x03: EntHelper('Raptor', 95, 3, 0, 1),
            0x04: EntHelper('Noximander', 35, 4, 0, 1),
            0x05: EntHelper('Fungal Slime', 25, 5, 0, 1),
            0x06: EntHelper('Walking Corpse', 55, 6, 0, 1),
            0x07: EntHelper('Acid Grubb', 70, 7, 0, 1),
            0x08: EntHelper('Timberland Giant', 140, 8, 0, 1),
            0x09: EntHelper('Goblin Hacker', 38, 9, 0, 1),
            0x0A: EntHelper('Goblin Archer', 45, 10, 0, 1),
            0x0B: EntHelper('Goblin Warlord', 75, 11, 0, 1),
            0x0C: EntHelper('Hive Drone', 40, 12, 0, 1),
            0x0D: EntHelper('Hive Queen', 100, 13, 0, 1),
            0x0E: EntHelper('Thug', 40, 14, 0, 1),
            0x0F: EntHelper('Dimensional Eye', 80, 15, 0, 1),
            0x10: EntHelper('Giant Arachnid', 70, 16, 0, 1),
            0x11: EntHelper('Dirachnid', 250, 17, 0, 1),
            0x12: EntHelper('Skeleton', 50, 18, 0, 1),
            0x13: EntHelper('Goblin Bombthug', 15, 19, 0, 1),
            0x14: EntHelper('Poltergeist', 60, 20, 0, 1),
            0x15: EntHelper('Barrea Mercenary', 90, 21, 0, 1),
            0x16: EntHelper('Taurax', 140, 22, 0, 1),
            0x17: EntHelper('Spire Guard', 300, 60, 0, 1),

            # NPCs
            0x33: EntHelper('Maddock', 15, 51, 1, 1),
            0x34: EntHelper('Michael', 36, 52, 1, 1),
            0x35: EntHelper('Farwick', 50, 53, 1, 1),
            0x36: EntHelper('Abygale', 25, 62, 1, 1),
            0x37: EntHelper('Eleanor *', 1, 55, 1, 2),
            0x38: EntHelper('Garrett *', 1, 50, 1, 2),
            0x39: EntHelper('Porter', 32, 56, 1, 1),
            0x3A: EntHelper('Oswell *', 1, 58, 1, 2),
            0x3B: EntHelper('Lilith', 130, 54, 1, 1),
            0x3C: EntHelper('Town Guard', 120, 60, 1, 1),
            0x3D: EntHelper('Gruzz', 16, 9, 1, 1),
            0x3E: EntHelper('Gatekeeper', 45, 60, 1, 1),
            0x3F: EntHelper('Eeru', 50, 65, 1, 1),
            0x40: EntHelper('Erik', 45, 53, 1, 1),
            0x41: EntHelper('Darkford Guard', 120, 60, 1, 1),
            0x42: EntHelper('Gunther', 85, 53, 1, 1),
            0x43: EntHelper('Leurik', 22, 65, 1, 1),
            0x44: EntHelper('Vault Master', 5, 9, 1, 1),
            0x45: EntHelper('Paul', 15, 51, 1, 1),
            0x46: EntHelper('Krista', 70, 57, 1, 1),
            0x47: EntHelper('Gamfari', 20, 64, 1, 1),
            0x48: EntHelper('Larrus *', 1, 66, 1, 2),
            0x49: EntHelper('Mary', 2, 63, 1, 1),
            0x4A: EntHelper('Vekkar *', 1, 67, 1, 2),
            0x4B: EntHelper('Jonathon', 36, 52, 1, 1),
            0x4C: EntHelper('Shady Character (1)', 90, 14, 1, 1),
            0x4D: EntHelper('Oolaseph *', 1, 54, 1, 2),
            0x4E: EntHelper('Vault Guard', 50, 60, 1, 1),
            0x4F: EntHelper('Vidar the Knife', 50, 14, 1, 1),
            0x50: EntHelper('Walter', 15, 68, 1, 1),
            0x51: EntHelper('Azure Guard', 120, 60, 1, 1),
            0x52: EntHelper('Captain Morgan', 120, 60, 1, 1),
            0x53: EntHelper('Erubor', 80, 69, 1, 1),
            0x54: EntHelper('Shadowmirk Acolyte', 15, 68, 1, 1),
            0x55: EntHelper('Phillip', 15, 65, 1, 1),
            0x56: EntHelper('Omar', 140, 8, 1, 1),
            0x57: EntHelper('Gramuk', 45, 70, 1, 1),
            0x58: EntHelper('Shady Character (2)', 110, 14, 1, 1),
            0x5A: EntHelper('Chancellor Malcolm *', 4, 71, 1, 2),
            0x5B: EntHelper('Sonya', 160, 59, 1, 1),
            0x5C: EntHelper('Aaron', 70, 61, 1, 1),
            0x5D: EntHelper('Penelope', 2, 62, 1, 1),
            0x5E: EntHelper('Siam', 80, 65, 1, 1),
            0x5F: EntHelper('William', 60, 51, 1, 1),
            0x60: EntHelper('Hesham', 60, 65, 1, 1)
        }

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

    def get_entitytable(self):
        """
        Returns a dict of entities
        """
        if self.entitytable is None:
            self.populate_datapak_info()
        return self.entitytable

    def get_entity(self, entid):
        """
        Returns the requested entity, or None if not found
        """
        if self.entitytable is None:
            self.populate_datapak_info()

        try:
            return self.entitytable[entid]
        except KeyError:
            return None


class B2EschalonData(EschalonData):
    """
    Book 2 specific Eschalon Data
    """
    empty_name = 'empty'
    random_name = 'random'


class B3EschalonData(EschalonData):
    """
    Book 3 specific Eschalon Data
    """
    empty_name = 'EMPTY'
    random_name = 'RANDOM'
