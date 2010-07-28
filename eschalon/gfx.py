#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2010 CJ Kucera
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

import os
import gtk
import math
import zlib
import cairo
import base64
import gobject
import cStringIO
from struct import unpack
from eschalon import constants as c
from eschalon.savefile import Savefile, LoadException

try:
    import czipfile as zipfile
    fast_zipfile = True
except ImportError:
    import eschalon.fzipfile as zipfile
    fast_zipfile = False

class GfxCache(object):
    """
    A class to hold graphic data, with resizing abilities and the like.
    It can return a Cairo surface (by default, via getimg()), or a GDK
    Pixbuf (via getimg_gdk()).  There's some code duplication between
    those two functions, which isn't ideal, but I didn't want to take the
    time to abstract the common stuff out.  So there.
    """

    def __init__(self, pngdata, width, height, cols, overlay_func=None):
        # First load the data as a Cairo surface
        self.surface = cairo.ImageSurface.create_from_png(cStringIO.StringIO(pngdata))

        if overlay_func:
            self.surface = overlay_func(self.surface, width, height, cols)
            df = cStringIO.StringIO()
            self.surface.write_to_png(df)
            pngdata = df.getvalue()
            df.close()

        # For ease-of-use, we're also going to import it to a GDK Pixbuf
        # This shouldn't hurt performance really since there's only a few files
        try:
            # On Windows, the Hive Queen graphic can't be loaded this way for
            # some reason.  See http://bugzilla.gnome.org/show_bug.cgi?id=575583
            # We try/except here to work around it; otherwise we can't load
            # 34_cave.map
            loader = gtk.gdk.PixbufLoader()
            loader.write(pngdata)
            loader.close()
            self.pixbuf = loader.get_pixbuf()
            loader = None
            self.gdkcache = {}
        except gobject.GError, e:
            self.gdkcache = None

        # Now assign the rest of our attributes
        self.width = width
        self.height = height
        self.cols = cols
        self.cache = {}

    def getimg(self, number, sizex=None, gdk=False):
        """ Grab an image from the cache, as a Cairo surface. """
        if (gdk):
            return self.getimg_gdk(number, sizex)
        number = number - 1
        row = math.floor(number / self.cols)
        col = number % self.cols
        if (number not in self.cache):
            copy_x_from = int(col*self.width)
            copy_y_from = int(row*self.height)
            if (copy_x_from+self.width > self.surface.get_width() or
                copy_y_from+self.height > self.surface.get_height()):
                return None
            self.cache[number] = {}
            self.cache[number]['orig'] = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
            ctx = cairo.Context(self.cache[number]['orig'])
            # Note the negative values here; nothing to be worried about.
            ctx.set_source_surface(self.surface, -copy_x_from, -copy_y_from)
            ctx.paint()
            self.cache[number][self.width] = self.cache[number]['orig']
        if (sizex is None):
            return self.cache[number]['orig']
        else:
            if (sizex not in self.cache[number]):
                sizey = (sizex*self.height)/self.width
                # This is crazy, seems like a million calls just to resize a bitmap
                if (sizex > sizey):
                    scale = float(self.width)/sizex
                else:
                    scale = float(self.height)/sizey
                self.cache[number][sizex] = cairo.ImageSurface(cairo.FORMAT_ARGB32, sizex, sizey)
                imgpat = cairo.SurfacePattern(self.cache[number]['orig'])
                scaler = cairo.Matrix()
                scaler.scale(scale, scale)
                imgpat.set_matrix(scaler)
                imgpat.set_filter(cairo.FILTER_BILINEAR)
                ctx = cairo.Context(self.cache[number][sizex])
                ctx.set_source(imgpat)
                ctx.paint()
            return self.cache[number][sizex]

    def getimg_gdk(self, number, sizex=None):
        """ Grab an image from the cache, as a GDK pixbuf """
        if (self.gdkcache is None):
            return None
        number = number - 1
        row = math.floor(number / self.cols)
        col = number % self.cols
        if (number not in self.gdkcache):
            copy_x_from = int(col*self.width)
            copy_y_from = int(row*self.height)
            if (copy_x_from+self.width > self.pixbuf.get_property('width') or
                copy_y_from+self.height > self.pixbuf.get_property('height')):
                return None
            self.gdkcache[number] = {}
            self.gdkcache[number]['orig'] = gtk.gdk.Pixbuf(self.pixbuf.get_colorspace(),
                    self.pixbuf.get_has_alpha(),
                    self.pixbuf.get_bits_per_sample(),
                    self.width, self.height)
            self.pixbuf.copy_area(copy_x_from,
                    copy_y_from,
                    self.width,
                    self.height,
                    self.gdkcache[number]['orig'],
                    0, 0)
            self.gdkcache[number][self.width] = self.gdkcache[number]['orig']
        if (sizex is None):
            return self.gdkcache[number]['orig']
        else:
            if (sizex not in self.gdkcache[number]):
                sizey = (sizex*self.height)/self.width
                self.gdkcache[number][sizex] = self.gdkcache[number]['orig'].scale_simple(sizex, sizey, gtk.gdk.INTERP_BILINEAR)
            return self.gdkcache[number][sizex]

class B1GfxEntCache(GfxCache):
    """
    A class to hold image data about entity graphics.  Mostly we're just
    overloading the constructor here, since we'd rather not hard-code what
    the various image sizes are.  Also, we can save some memory by lopping
    off much of the loaded image.
    """
    def __init__(self, pngdata, cols=15, rows=8):

        # Read in the data as usual, with junk for width and height
        super(B1GfxEntCache, self).__init__(pngdata, -1, -1, 1)

        # ... and now that we have the image dimensions, fix that junk
        imgwidth = self.surface.get_width()
        imgheight = self.surface.get_height()
        self.width = int(imgwidth/cols)
        self.height = int(imgheight/rows)

        # Some information on size scaling
        self.size_scale = self.width/52.0

        # Lop off the data we don't need, to save on memory usage
        newsurf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, imgheight)
        newctx = cairo.Context(newsurf)
        newctx.set_source_surface(self.surface, 0, 0)
        newctx.paint()
        self.surface = newsurf

        # (and on our pixbuf copy as well)
        if (self.gdkcache is not None):
            newbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.width, imgheight)
            self.pixbuf.copy_area(0, 0, self.width, imgheight, newbuf, 0, 0)
            self.pixbuf = newbuf

class B2GfxEntCache(GfxCache):
    """
    A class to hold image data about entity graphics.  We're doing all kinds
    of things here to support Book 2.
    """
    def __init__(self, ent, pngdata):

        # Read in the data as usual, with junk for width and height
        super(B2GfxEntCache, self).__init__(pngdata, -1, -1, 1)

        # Figure out various dimensions
        imgwidth = self.surface.get_width()
        imgheight = self.surface.get_height()
        self.width = ent.width
        self.height = ent.height
        cols = int(imgwidth/ent.width)
        #print '%s - %d x %d: %d cols' % (ent.name, self.width, self.height, cols)

        # Some information on size scaling
        self.size_scale = self.width/64.0

        # Construct an abbreviated image with just one frame per direction
        newsurf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height*ent.dirs)
        newctx = cairo.Context(newsurf)
        newctx.save()
        for i in range(ent.dirs):
            frame = ent.frames * i
            col = (frame % cols)
            row = int(frame / cols)
            newctx.set_operator(cairo.OPERATOR_SOURCE)
            newctx.set_source_surface(self.surface, -col*self.width, -row*self.height + (i*self.height))
            newctx.rectangle(0, i*self.height, self.width, self.height)
            newctx.fill()
        newctx.restore()
        self.surface = newsurf
        #newsurf.write_to_png('computed_%s' % (ent.gfxfile))

        # (and on our pixbuf copy as well)
        if (self.gdkcache is not None):
            self.pixbuf = Gfx.surface_to_pixbuf(newsurf)

class SingleImageGfxCache(GfxCache):
    """
    Class to take care of "huge" images, mostly, in which we just want to cache resized graphics.
    Only used for Book 2 at the moment, hence our "64" hardcode down below.
    """
    def __init__(self, pngdata):

        # Read the data as usual, with junk for width and height
        super(SingleImageGfxCache, self).__init__(pngdata, -1, -1, 1)

        # And now set the image dimensions appropriately
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()
        self.size_scale = self.width/64.0

class PakIndex(object):
    """ A class to hold information on an individual file in the pak. """

    def __init__(self, data):
        (self.size_compressed,
                self.abs_index,
                self.size_real,
                self.unknowni1) = unpack('<IIII', data[:16])
        self.filename = data[16:]
        self.filename = self.filename[:self.filename.index("\x00")]

class Gfx(object):
    """ A class to hold graphics data. """

    wall_types = {}
    TYPE_NONE = -1
    TYPE_OBJ = 1
    TYPE_WALL = 2
    TYPE_TREE = 3

    def __init__(self, prefs, datadir):
        """ A fresh object with no data. """

        self.prefs = prefs
        self.datadir = datadir

        # Store whether or not we have fast zip decryption
        self.fast_zipfile = fast_zipfile

        # wtf @ needing this (is the same for B1 and B2)
        self.treemap = {
            251: 4,
            252: 5,
            253: 1,
            254: 2,
            255: 3
            }

        # Some graphic-specific indexes/flags
        self.floorcache = None
        self.decalcache = None
        self.objcache1 = None
        self.objcache2 = None
        self.objcache3 = None
        self.objcache4 = None
        self.objdecalcache = None
        self.avatarcache = {}
        self.entcache = {}
        self.flamecache = None

        # Now do an initial read
        self.loaded = False
        self.initialread()

    def initialread(self):
        """
        Anything that needs to be done to initialize loading
        the graphics.  Should be overridden by implementing classes
        if needed
        """
        self.loaded = True

    @staticmethod
    def surface_to_pixbuf(surface):
        """
        Helper function to convert a Cairo surface to a GDK Pixbuf.  It's
        very slow, don't use it if you need speed.  It's probably about as
        fast as you're going to get, though, since every other method I've
        found would require you to loop through and fix each pixel in the
        pixbuf afterwards.
        """
        df = cStringIO.StringIO()
        surface.write_to_png(df)
        loader = gtk.gdk.PixbufLoader()
        loader.write(df.getvalue())
        loader.close()
        df.close()
        return loader.get_pixbuf()

    @staticmethod
    def new(book, prefs, datadir):
        """
        Returns a B1Gfx or B2Gfx object, depending on the book that we're working with
        """
        if book == 1:
            return B1Gfx(prefs, datadir)
        else:
            return B2Gfx(prefs, datadir)

class B1Gfx(Gfx):
    """
    Grphics structure for Book 1
    """

    book = 1
    wall_types = {}
    squarebuf_mult = 1
    item_dim = 42
    item_cols = 10
    item_rows = 24
    square_width = 52
    square_height = 26
    floor_cols = 6
    floor_rows = 32
    decal_cols = 6
    decal_rows = 32
    obj_a_width = 52
    obj_a_height = 52
    obj_a_cols = 6
    obj_a_rows = 16
    obj_a_offset = 1
    obj_b_width = 52
    obj_b_height = 78
    obj_b_cols = 6
    obj_b_rows = 10
    obj_b_offset = 101
    obj_c_width = 52
    obj_c_height = 78
    obj_c_cols = 6
    obj_c_rows = 10
    obj_c_offset = 161
    obj_d_width = 52
    obj_d_height = 130
    obj_d_cols = 5
    obj_d_rows = 1
    obj_d_offset = 251
    walldecal_cols = 6
    walldecal_rows = 10

    def __init__(self, prefs, datadir):

        # Wall object types
        for i in range(161):
            self.wall_types[i] = self.TYPE_OBJ
        for i in range(161, 251):
            self.wall_types[i] = self.TYPE_OBJ
        for i in range(251, 256):
            self.wall_types[i] = self.TYPE_TREE

        # Restricted entities (only one direction)
        self.restrict_ents = [50, 55, 58, 66, 67, 71]

        # Book 1 specific vars (just the PAK structure stuff)
        self.unknownh1 = -1
        self.unknownh2 = -1
        self.numfiles = -1
        self.compressed_idx_size = -1
        self.unknowni1 = -1
        self.fileindex = {}
        self.zeroindex = -1

        # Book 1 specific caches
        self.itemcache = None

        # Graphics PAK file
        self.pakloc = os.path.join(prefs.get_str('paths', 'gamedir'), 'gfx.pak')
        self.df = Savefile(self.pakloc)

        # Finally call the parent constructor
        super(B1Gfx, self).__init__(prefs, datadir)

    def readfile(self, filename):
        """ Reads a given filename out of the PAK. """
        if self.loaded:
            if (filename in self.fileindex):
                self.df.open_r()
                self.df.seek(self.zeroindex + self.fileindex[filename].abs_index)
                # On Windows, we need to specify bufsize or memory gets clobbered
                filedata = zlib.decompress(
                    self.df.read(self.fileindex[filename].size_compressed),
                    15,
                    self.fileindex[filename].size_real)
                self.df.close()
                return filedata
            else:
                raise LoadException('Filename %s not found in archive' % (filename))
        else:
            raise LoadException('PAK Index has not been loaded')

    def initialread(self):
        """ Read in the main file index. """

        df = self.df
        df.open_r()
        header = df.read(4)
        if (header != '!PAK'):
            df.close()
            raise LoadException('Invalid PAK header')
        
        # Initial Values
        self.unknownh1 = df.readshort()
        self.unknownh2 = df.readshort()
        self.numfiles = df.readint()
        self.compressed_idx_size = df.readint()
        self.unknowni1 = df.readint()

        # Now load in the index
        decobj = zlib.decompressobj()
        indexdata = decobj.decompress(df.read())
        self.zeroindex = df.tell() - len(decobj.unused_data)
        decobj = None
        for i in range(self.numfiles):
            index = PakIndex(indexdata[:272])
            indexdata = indexdata[272:]
            self.fileindex[index.filename] = index

        # Close and clean up
        df.close()
        self.loaded = True

    def get_item(self, item, size=None, gdk=True):
        if (self.itemcache is None):
            self.itemcache = GfxCache(self.readfile('items_mastersheet.png'), 42, 42, 10)
        return self.itemcache.getimg(item.pictureid+1, size, gdk)

    def get_floor(self, floornum, size=None, gdk=False):
        if (floornum == 0):
            return None
        if (self.floorcache is None):
            self.floorcache = GfxCache(self.readfile('iso_tileset_base.png'), 52, 26, 6)
        return self.floorcache.getimg(floornum, size, gdk)

    def get_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.decalcache is None):
            self.decalcache = GfxCache(self.readfile('iso_tileset_base_decals.png'), 52, 26, 6)
        return self.decalcache.getimg(decalnum, size, gdk)

    # Returns a tuple, first item is the surface, second is the extra height to add while drawing
    def get_object(self, objnum, size=None, gdk=False, treeset=0):
        """
        Note that we ignore the treeset flag in book 1
        """
        # TODO: switch to using the wall_types stuff
        if (objnum == 0):
            return (None, 0, 0)
        if (objnum < 101):
            if (self.objcache1 is None):
                self.objcache1 = GfxCache(self.readfile('iso_tileset_obj_a.png'), 52, 52, 6)
            return (self.objcache1.getimg(objnum, size, gdk), 1, 0)
        elif (objnum < 161):
            if (self.objcache2 is None):
                self.objcache2 = GfxCache(self.readfile('iso_tileset_obj_b.png'), 52, 78, 6)
            return (self.objcache2.getimg(objnum-100, size, gdk), 2, 0)
        elif (objnum < 251):
            if (self.objcache3 is None):
                self.objcache3 = GfxCache(self.readfile('iso_tileset_obj_c.png'), 52, 78, 6)
            return (self.objcache3.getimg(objnum-160, size, gdk), 2, 0)
        else:
            if (self.objcache4 is None):
                self.objcache4 = GfxCache(self.readfile('iso_trees.png'), 52, 130, 5)
            if (objnum in self.treemap):
                return (self.objcache4.getimg(self.treemap[objnum], size, gdk), 4, 0)
            else:
                return (None, 4, 0)

    def get_object_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.objdecalcache is None):
            self.objdecalcache = GfxCache(self.readfile('iso_tileset_obj_decals.png'), 52, 78, 6)
        return self.objdecalcache.getimg(decalnum, size, gdk)

    def get_flame(self, size=None, gdk=False):
        """
        Grabs the flame graphic, so it's clear when viewing maps.  I provide my own
        image here instead of using the game's because the file bundled with the game
        doesn't have transparency information, and I don't feel like doing a conversion.
        """
        if (self.flamecache is None):
            df = open(os.path.join(self.datadir, 'torch_single.png'), 'rb')
            flamedata = df.read()
            df.close()
            self.flamecache = B1GfxEntCache(flamedata, 1, 1)
        # TODO: I don't like hardcoding "52" here
        if (size is None):
            size = 52
        return self.flamecache.getimg(1, int(size*self.flamecache.size_scale), gdk)

    def get_entity(self, entnum, direction, size=None, gdk=False):
        entnum = c.entitytable[entnum].gfxfile
        if (entnum not in self.entcache):
            filename = 'mo%d.png' % (entnum)
            if (entnum in self.restrict_ents):
                self.entcache[entnum] = B1GfxEntCache(self.readfile(filename), 2, 1)
            else:
                self.entcache[entnum] = B1GfxEntCache(self.readfile(filename))
        cache = self.entcache[entnum]
        # TODO: I don't like hardcoding "52" here...
        if (size is None):
            size = 52
        return cache.getimg(direction, int(size*cache.size_scale), gdk)

    def get_avatar(self, avatarnum):
        if (avatarnum < 0 or avatarnum > 7):
            return None
        if (avatarnum not in self.avatarcache):
            if (avatarnum == 7):
                if (os.path.exists(os.path.join(self.prefs.get_str('paths', 'gamedir'), 'mypic.png'))):
                    self.avatarcache[avatarnum] = gtk.gdk.pixbuf_new_from_file(os.path.join(self.prefs.get_str('paths', 'gamedir'), 'mypic.png'))
                else:
                    return None
            else:
                self.avatarcache[avatarnum] = GfxCache(self.readfile('%d.png' % (avatarnum)), 60, 60, 1).pixbuf
        return self.avatarcache[avatarnum]

class B2Gfx(Gfx):
    """
    Graphics structure for Book 2
    """

    book = 2
    wall_types = {}
    squarebuf_mult = 1.5
    item_dim = 50
    item_cols = 10
    item_rows = 10
    square_width = 64
    square_height = 32
    floor_cols = 8
    floor_rows = 16
    decal_cols = 16
    decal_rows = 16
    obj_a_width = 64
    obj_a_height = 64
    obj_a_cols = 16
    obj_a_rows = 10
    obj_a_offset = 1
    obj_c_width = 64
    obj_c_height = 96
    obj_c_cols = 16
    obj_c_rows = 10
    obj_c_offset = 256
    obj_d_width = 96
    obj_d_height = 160
    obj_d_cols = 5
    obj_d_rows = 1
    obj_d_offset = 251
    walldecal_cols = 16
    walldecal_rows = 10

    def __init__(self, prefs, datadir):

        # Import Crypto stuff
        try:
            from Crypto.Cipher import AES
            self.aesc = AES
        except:
            raise Exception('Book 2 Graphics requires pycrypto, please install it: http://www.dlitz.net/software/pycrypto/')
        self.prep_crypt()

        # Wall object types
        for i in range(251):
            self.wall_types[i] = self.TYPE_OBJ
        for i in range(251, 256):
            self.wall_types[i] = self.TYPE_TREE
        for i in range(256, 513):
            self.wall_types[i] = self.TYPE_WALL

        # Book 2 specific caches
        self.treecache = [ None, None, None ]
        self.hugegfxcache = {}
        self.itemcache = {
                'armor': None,
                'magic': None,
                'misc': None,
                'weapons': None
            }
        self.itemcache_overlayfunc = {
                'armor': self.item_overlayfunc_armor,
                'magic': None,
                'misc': None,
                'weapons': self.item_overlayfunc_weapon
            }
        self.zappercache = None

        # Item type graphic file lookups
        self.itemtype_gfxcache_idx = {}
        for num in range(50):
            self.itemtype_gfxcache_idx[num] = 'misc'
        for num in range(1, 3):
            self.itemtype_gfxcache_idx[num] = 'weapons'
        for num in range(3, 11):
            self.itemtype_gfxcache_idx[num] = 'armor'
        for num in range(11, 16) + [17]:
            self.itemtype_gfxcache_idx[num] = 'magic'
        
        # Store our gamedir
        self.gamedir = prefs.get_str('paths', 'gamedir_b2')

        # Finally call the parent constructor
        super(B2Gfx, self).__init__(prefs, datadir)

    def item_overlayfunc(self, surface, width, height, cols, type):
        """
        In Book 2, the Weapon and Armor graphics don't have a background, which looks
        a little odd in the GUI.  So we construct them based on the given elements in
        the data dir.
        """

        # First load in the background and its frame
        frame = self.readfile('icon_frame.png')
        background = self.readfile('%s_icon_blank.png' % (type))
        framesurf = cairo.ImageSurface.create_from_png(cStringIO.StringIO(frame))
        backsurf = cairo.ImageSurface.create_from_png(cStringIO.StringIO(background))

        # Now create a new surface and tile the background over the whole thing
        newsurf = cairo.ImageSurface(cairo.FORMAT_ARGB32, surface.get_width(), surface.get_height())
        newctx = cairo.Context(newsurf)
        rows = int(surface.get_height()/height)
        for row in range(rows):
            for col in range(cols):
                newctx.set_source_surface(backsurf, col*width, row*height)
                newctx.rectangle(col*width, row*height, width, height)
                newctx.paint()

        # Overlay our passed-in surface on top
        newctx.set_source_surface(surface, 0, 0)
        newctx.rectangle(0, 0, surface.get_width(), surface.get_height())
        newctx.paint()

        # Now tile the frame on top of every item
        for row in range(rows):
            for col in range(cols):
                newctx.set_source_surface(framesurf, col*width, row*height)
                newctx.rectangle(col*width, row*height, width, height)
                newctx.paint()

        return newsurf

    def item_overlayfunc_armor(self, surface, width, height, cols):
        return self.item_overlayfunc(surface, width, height, cols, 'armor')

    def item_overlayfunc_weapon(self, surface, width, height, cols):
        return self.item_overlayfunc(surface, width, height, cols, 'weapon')

    def prep_crypt(self):
        # Yes, I'm fully aware that all this munging about is merely obfuscation and
        # wouldn't actually prevent anyone from getting to the data, but I feel
        # obligated to go through the motions regardless.  Hi there!  Note that I 
        # *did* get BW's permission to access the graphics data this way.
        s = base64.urlsafe_b64decode(c.s)
        d = base64.urlsafe_b64decode(c.d)
        iv = d[:16]
        self.aesenc = d[16:]
        self.aes = self.aesc.new(s, self.aesc.MODE_CBC, iv)

    def readfile(self, filename, dir='gfx'):
        """
        Reads a given filename.
        """
        filename = '%s/%s' % (dir, filename)
        if self.loaded:
            try:
                return self.zip.read(filename)
            except KeyError:
                raise LoadException('Filename %s not found in datapak!' % (filename))
        else:
            raise LoadException('We haven\'t initialized ourselves yet')

    def get_item(self, item, size=None, gdk=True):
        if item.type not in self.itemtype_gfxcache_idx:
            idx = 'misc'
        else:
            idx = self.itemtype_gfxcache_idx[item.type]
        if (self.itemcache[idx] is None):
            self.itemcache[idx] = GfxCache(self.readfile('%s_sheet.png' % (idx)), 50, 50, 10, self.itemcache_overlayfunc[idx])
        return self.itemcache[idx].getimg(item.pictureid+1, size, gdk)

    def get_floor(self, floornum, size=None, gdk=False):
        if (floornum == 0):
            return None
        if (self.floorcache is None):
            self.floorcache = GfxCache(self.readfile('iso_base.png'), 64, 32, 8)
        return self.floorcache.getimg(floornum, size, gdk)

    def get_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.decalcache is None):
            self.decalcache = GfxCache(self.readfile('iso_basedecals.png'), 64, 32, 16)
        return self.decalcache.getimg(decalnum, size, gdk)

    # Returns a tuple, first item is the surface, second is the extra height to add while drawing
    def get_object(self, objnum, size=None, gdk=False, treeset=0):
        if (objnum == 0):
            return (None, 0, 0)
        try:
            walltype = self.wall_types[objnum]
        except TypeError:
            #print "unknown objnum: %d" % (objnum)
            return (None, 0, 0)
        if (walltype == self.TYPE_OBJ):
            if (self.objcache1 is None):
                self.objcache1 = GfxCache(self.readfile('iso_obj.png'), 64, 64, 16)
            return (self.objcache1.getimg(objnum, size, gdk), 1, 0)
        elif (walltype == self.TYPE_WALL):
            if (self.objcache2 is None):
                self.objcache2 = GfxCache(self.readfile('iso_walls.png'), 64, 96, 16)
            return (self.objcache2.getimg(objnum-255, size, gdk), 2, 0)
        elif (walltype == self.TYPE_TREE):
            if (self.treecache[treeset] is None):
                self.treecache[treeset] = GfxCache(self.readfile('iso_trees%d.png' % (treeset)), 96, 160, 5)
            if (objnum in self.treemap):
                # note the size difference for Book 2 trees (50% wider)
                if not size:
                    size = 64
                offset = -int(size/4)
                size = int(size * 1.5)
                return (self.treecache[treeset].getimg(self.treemap[objnum], size, gdk), 4, offset)
            else:
                return (None, 4, 0)

    def get_object_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.objdecalcache is None):
            self.objdecalcache = GfxCache(self.readfile('iso_objdecals.png'), 64, 96, 16)
        return self.objdecalcache.getimg(decalnum, size, gdk)

    def get_flame(self, size=None, gdk=False):
        """
        Grabs the flame graphic, so it's clear when viewing maps.  I provide my own
        image here instead of using the game's because the file bundled with the game
        doesn't have transparency information, and I don't feel like doing a conversion.
        """
        if (self.flamecache is None):
            df = open(os.path.join(self.datadir, 'torch_single.png'), 'rb')
            flamedata = df.read()
            df.close()
            # TODO: This is, um, highly improper.
            self.flamecache = B1GfxEntCache(flamedata, 1, 1)
            #self.flamecache = SingleImageGfxCache(flamedata)
        # TODO: I don't like hardcoding "64" here
        if (size is None):
            size = 64
        return self.flamecache.getimg(1, int(size*self.flamecache.size_scale), gdk)

    def get_zapper(self, size=None, gdk=False):
        """
        Grabs a zapper image.
        """
        if (self.zappercache is None):
            df = open(os.path.join(self.datadir, 'zappy_single.png'), 'rb')
            zapperdata = df.read()
            df.close()
            self.zappercache = SingleImageGfxCache(zapperdata)
        # TODO: I don't like hardcoding "64" here
        if (size is None):
            size = 64
        return self.zappercache.getimg(1, int(size*self.zappercache.size_scale), gdk)

    def get_huge_gfx(self, file, size=None, gdk=False):
        """
        Grabs an arbitrary graphic file from our pool (used for the "huge" graphics like Hammerlorne,
        Corsair ships, etc, in Book 2)
        """
        # TODO: get_flame should probably just call this
        if file not in self.hugegfxcache:
            if (file.find('/') != -1 or file.find('..') != -1 or file.find('\\') != -1):
                return None
            self.hugegfxcache[file] = SingleImageGfxCache(self.readfile(file))
        # Not fond of hardcoding "64" here
        if (size is None):
            size = 64
        return self.hugegfxcache[file].getimg(1, int(size*self.hugegfxcache[file].size_scale), gdk)

    def get_entity(self, entnum, direction, size=None, gdk=False):
        ent = c.entitytable[entnum]
        if (entnum not in self.entcache):
            filename = ent.gfxfile
            self.entcache[entnum] = B2GfxEntCache(ent, self.readfile(filename))
        cache = self.entcache[entnum]
        # TODO: I don't like hardcoding "64" here...
        if (size is None):
            size = 64
        return cache.getimg(direction, int(size*cache.size_scale), gdk)

    def get_avatar(self, avatarnum):
        # TODO: fix custom pic logic here
        if (avatarnum < 0 or avatarnum > 12):
            return None
        if (avatarnum not in self.avatarcache):
            if (avatarnum == 0xFFFFFFFF):
                if (os.path.exists(os.path.join(self.gamedir, 'mypic.png'))):
                    self.avatarcache[avatarnum] = gtk.gdk.pixbuf_new_from_file(os.path.join(self.gamedir, 'mypic.png'))
                else:
                    return None
            else:
                self.avatarcache[avatarnum] = GfxCache(self.readfile('%d.png' % (avatarnum)), 60, 60, 1).pixbuf
        return self.avatarcache[avatarnum]

    def initialread(self):
        plain = self.aes.decrypt(self.aesenc)
        pad = ord(plain[-1])
        text = plain[:-pad]
        
        self.zip = zipfile.ZipFile(os.path.join(self.gamedir, 'datapak'), 'r')
        self.zip.setpassword(text)

        self.loaded = True
