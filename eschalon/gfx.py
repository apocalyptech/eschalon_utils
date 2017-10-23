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


import io
import logging
import math
import os
import zlib
from struct import unpack


from typing import Set, Any, Dict
import cairo
from gi.repository import GdkPixbuf

from eschalon.savefile import LoadException, Savefile

LOG = logging.getLogger(__name__)


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
        self.surface = cairo.ImageSurface.create_from_png(
            io.BytesIO(pngdata))

        if overlay_func:
            self.surface = overlay_func(self.surface, width, height, cols)
            df = io.BytesIO()
            self.surface.write_to_png(df)
            pngdata = df.getvalue()
            df.close()

        # For ease-of-use, we're also going to import it to a GDK Pixbuf
        # This shouldn't hurt performance really since there's only a few files
        loader = GdkPixbuf.PixbufLoader()
        loader.write(pngdata)
        loader.close()
        self.pixbuf = loader.get_pixbuf()
        self.gdkcache = {}

        # Now assign the rest of our attributes
        self.width = width
        self.height = height
        self.cols = cols
        self.cache = {}

    def getimg(self, number, sizex=None, gdk=False):
        """ Grab an image from the cache, as a Cairo surface. """
        if (gdk):
            return self.getimg_gdk(number, sizex)
        number -= 1
        row = math.floor(number / self.cols)
        col = number % self.cols
        if (number not in self.cache):
            copy_x_from = int(col * self.width)
            copy_y_from = int(row * self.height)
            if (copy_x_from + self.width > self.surface.get_width() or
                    copy_y_from + self.height > self.surface.get_height()):
                return None
            self.cache[number] = {}
            self.cache[number]['orig'] = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, self.width, self.height)
            ctx = cairo.Context(self.cache[number]['orig'])
            # Note the negative values here; nothing to be worried about.
            ctx.set_source_surface(self.surface, -copy_x_from, -copy_y_from)
            ctx.paint()
            self.cache[number][self.width] = self.cache[number]['orig']
        if (sizex is None):
            return self.cache[number]['orig']
        else:
            if (sizex not in self.cache[number]):
                sizey = (sizex * self.height) / self.width
                # This is crazy, seems like a million calls just to resize a bitmap
                if (sizex > sizey):
                    scale = float(self.width) / sizex
                else:
                    scale = float(self.height) / sizey
                self.cache[number][sizex] = cairo.ImageSurface(
                    cairo.FORMAT_ARGB32, sizex, sizey)
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
        number -= 1
        row = math.floor(number // self.cols)
        col = number % self.cols
        if (number not in self.gdkcache):
            copy_x_from = int(col * self.width)
            copy_y_from = int(row * self.height)
            if (copy_x_from + self.width > self.pixbuf.get_property('width') or
                    copy_y_from + self.height > self.pixbuf.get_property('height')):
                return None
            self.gdkcache[number] = {}
            self.gdkcache[number]['orig'] = GdkPixbuf.Pixbuf(self.pixbuf.get_colorspace(),
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
            if sizex not in self.gdkcache[number]:
                sizey = (sizex * self.height) // self.width
                self.gdkcache[number][sizex] = self.gdkcache[number]['orig'].scale_simple(
                    sizex, sizey, GdkPixbuf.InterpType.BILINEAR)
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
        self.width = int(imgwidth / cols)
        self.height = int(imgheight / rows)

        # Some information on size scaling
        self.size_scale = self.width / 52.0

        # Lop off the data we don't need, to save on memory usage
        newsurf = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, self.width, imgheight)
        newctx = cairo.Context(newsurf)
        newctx.set_source_surface(self.surface, 0, 0)
        newctx.paint()
        self.surface = newsurf

        # (and on our pixbuf copy as well)
        newbuf = GdkPixbuf.Pixbuf(
            GdkPixbuf.Colorspace.RGB, True, 8, self.width, imgheight)
        self.pixbuf.copy_area(0, 0, self.width, imgheight, newbuf, 0, 0)
        self.pixbuf = newbuf


class B23GfxEntCache(GfxCache):
    """
    A class to hold image data about entity graphics.  We're doing all kinds
    of things here to support Book 2.
    """

    def __init__(self, ent, pngdata):

        # Read in the data as usual, with junk for width and height
        super(B23GfxEntCache, self).__init__(pngdata, -1, -1, 1)

        # Figure out various dimensions
        imgwidth = self.surface.get_width()
        imgheight = self.surface.get_height()
        self.width = ent.width
        self.height = ent.height
        cols = int(imgwidth / ent.width)
        # print '%s - %d x %d: %d cols' % (ent.name, self.width, self.height, cols)

        # Some information on size scaling
        self.size_scale = self.width / 64.0

        # Construct an abbreviated image with just one frame per direction
        newsurf = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, self.width, self.height * ent.dirs)
        newctx = cairo.Context(newsurf)
        newctx.save()
        for i in range(ent.dirs):
            frame = ent.frames * i
            col = (frame % cols)
            row = int(frame / cols)
            newctx.set_operator(cairo.OPERATOR_SOURCE)
            newctx.set_source_surface(
                self.surface, -col * self.width, -row * self.height + (i * self.height))
            newctx.rectangle(0, i * self.height, self.width, self.height)
            newctx.fill()
        newctx.restore()
        self.surface = newsurf
        #newsurf.write_to_png('computed_%s' % (ent.gfxfile))

        # (and on our pixbuf copy as well)
        self.pixbuf = Gfx.surface_to_pixbuf(newsurf)


class SingleImageGfxCache(GfxCache):
    """
    Class to take care of "huge" images, mostly, in which we just want to cache resized graphics.
    Only used for Book 2 at the moment, hence our "64" hardcode down below.
    """

    def __init__(self, pngdata, scale=64.0):

        # Read the data as usual, with junk for width and height
        super(SingleImageGfxCache, self).__init__(pngdata, -1, -1, 1)

        # And now set the image dimensions appropriately
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()
        self.size_scale = self.width / scale


class PakIndex(object):
    """ A class to hold information on an individual file in the pak. """

    def __init__(self, data):
        (self.size_compressed,
         self.abs_index,
         self.size_real,
         self.unknowni1) = unpack('<IIII', data[:16])
        self.filename = data[16:]
        self.filename = self.filename[:self.filename.index(b"\x00")].decode("UTF-8")


class Gfx(object):
    """ A class to hold graphics data. """

    wall_types: Dict[Any, Any] = {}
    wall_gfx_group: Dict[Any, Any] = {}
    TYPE_NONE = -1
    TYPE_OBJ = 1
    TYPE_WALL = 2
    TYPE_TREE = 3

    def __init__(self, datadir, eschalondata):
        """
        A fresh object with no data.
        "datadir" is the path to our utilities "data" dir
        "eschalondata" is an EschalonData object where we can pull files from
        """

        self.datadir = datadir
        self.eschalondata = eschalondata

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
        self.initialread()

    def initialread(self):
        """
        Anything that needs to be done to initialize loading
        the graphics.  Should be overridden by implementing classes
        if needed
        """
        pass

    @staticmethod
    def surface_to_pixbuf(surface):
        """
        Helper function to convert a Cairo surface to a GDK Pixbuf.  It's
        very slow, don't use it if you need speed.  It's probably about as
        fast as you're going to get, though, since every other method I've
        found would require you to loop through and fix each pixel in the
        pixbuf afterwards.
        """
        df = io.BytesIO()
        surface.write_to_png(df)
        loader = GdkPixbuf.PixbufLoader()
        loader.write(df.getvalue())
        loader.close()
        df.close()
        return loader.get_pixbuf()

    @staticmethod
    def new(book, datadir, eschalondata):
        """
        Returns a B1Gfx or B2Gfx object, depending on the book that we're working with
        """
        if book == 1:
            return B1Gfx(datadir, eschalondata)
        elif book == 2:
            return B2Gfx(datadir, eschalondata)
        elif book == 3:
            return B3Gfx(datadir, eschalondata)
        else:
            raise LoadException(
                'Book number must be 1, 2, or 3 (passed %d)' % (book))


class B1Gfx(Gfx):
    """
    Grphics structure for Book 1
    """

    book = 1
    wall_types = {}
    wall_gfx_group = {}
    tilebuf_mult = 1
    item_dim = 42
    item_cols = 10
    item_rows = 24
    tile_width = 52
    tile_height = 26
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

    GFX_SET_A = 1
    GFX_SET_B = 2
    GFX_SET_C = 3
    GFX_SET_TREE = 4

    def __init__(self, datadir, eschalondata):

        # Wall graphic groupings
        for i in range(101):
            self.wall_gfx_group[i] = self.GFX_SET_A
        for i in range(101, 161):
            self.wall_gfx_group[i] = self.GFX_SET_B
        for i in range(161, 251):
            self.wall_gfx_group[i] = self.GFX_SET_C
        for i in range(251, 256):
            self.wall_gfx_group[i] = self.GFX_SET_TREE

        # Wall object types
        for i in (list(range(127)) + list(range(132, 142)) + list(range(143, 153)) +
                  list(range(154, 161)) + list(range(214, 251))):
            self.wall_types[i] = self.TYPE_OBJ
        for i in range(161, 214):
            self.wall_types[i] = self.TYPE_WALL
        for i in (list(range(251, 256)) + list(range(127, 132)) + [142, 153]):
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
        self.pakloc = os.path.join(eschalondata.gamedir, 'gfx.pak')
        if os.path.isfile(self.pakloc):
            self.df = Savefile(self.pakloc)
        else:
            self.df = None

        # Set our loaded status
        self.loaded = False

        # Finally call the parent constructor
        super(B1Gfx, self).__init__(datadir, eschalondata)

    def readfile(self, filename: str) -> object:
        """ Reads a given filename out of the PAK. """
        if self.loaded:
            filepath = os.path.join(
                self.eschalondata.gamedir, 'packedgraphics', filename)
            if os.path.isfile(filepath):
                return open(filepath, 'rb').read()
            if filename in self.fileindex:
                self.df.open_r()
                self.df.seek(self.zeroindex +
                             self.fileindex[filename].abs_index)
                # On Windows, we need to specify bufsize or memory gets clobbered
                filedata = zlib.decompress(
                    self.df.read(self.fileindex[filename].size_compressed),
                    15,
                    self.fileindex[filename].size_real)
                self.df.close()
                return filedata
            else:
                raise LoadException(
                    'Filename %s not found in archive' % (filename))
        else:
            raise LoadException('PAK Index has not been loaded')

    def initialread(self):
        """ Read in the main file index. """

        df = self.df
        if df is None:
            self.loaded = True
            return

        df.open_r()
        header = df.read(4)
        if (header != b'!PAK'):
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
        for i in range(self.numfiles):
            index = PakIndex(indexdata[:272])
            indexdata = indexdata[272:]
            self.fileindex[index.filename] = index

        # Close and clean up
        df.close()
        self.loaded = True

    def get_item(self, item, size=None, gdk=True):
        if (self.itemcache is None):
            self.itemcache = GfxCache(self.readfile(
                'items_mastersheet.png'), 42, 42, 10)
        return self.itemcache.getimg(item.pictureid + 1, size, gdk)

    def get_floor(self, floornum, size=None, gdk=False):
        if (floornum == 0):
            return None
        if (self.floorcache is None):
            self.floorcache = GfxCache(self.readfile(
                'iso_tileset_base.png'), 52, 26, 6)
        return self.floorcache.getimg(floornum, size, gdk)

    def get_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.decalcache is None):
            self.decalcache = GfxCache(self.readfile(
                'iso_tileset_base_decals.png'), 52, 26, 6)
        return self.decalcache.getimg(decalnum, size, gdk)

    # Returns a tuple, first item is the surface, second is the extra height to add while drawing
    def get_object(self, objnum, size=None, gdk=False, treeset=0):
        """
        Note that we ignore the treeset flag in book 1
        """
        if (objnum == 0):
            return (None, 0, 0)
        try:
            gfxgroup = self.wall_gfx_group[objnum]
        except KeyError:
            return (None, 0, 0)
        if gfxgroup == self.GFX_SET_A:
            if (self.objcache1 is None):
                self.objcache1 = GfxCache(self.readfile(
                    'iso_tileset_obj_a.png'), 52, 52, 6)
            return (self.objcache1.getimg(objnum, size, gdk), 1, 0)
        elif gfxgroup == self.GFX_SET_B:
            if (self.objcache2 is None):
                self.objcache2 = GfxCache(self.readfile(
                    'iso_tileset_obj_b.png'), 52, 78, 6)
            return (self.objcache2.getimg(objnum - 100, size, gdk), 2, 0)
        elif gfxgroup == self.GFX_SET_C:
            if (self.objcache3 is None):
                self.objcache3 = GfxCache(self.readfile(
                    'iso_tileset_obj_c.png'), 52, 78, 6)
            return (self.objcache3.getimg(objnum - 160, size, gdk), 2, 0)
        else:
            if (self.objcache4 is None):
                self.objcache4 = GfxCache(
                    self.readfile('iso_trees.png'), 52, 130, 5)
            if (objnum in self.treemap):
                return (self.objcache4.getimg(self.treemap[objnum], size, gdk), 4, 0)
            else:
                return (None, 4, 0)

    def get_object_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.objdecalcache is None):
            self.objdecalcache = GfxCache(self.readfile(
                'iso_tileset_obj_decals.png'), 52, 78, 6)
        return self.objdecalcache.getimg(decalnum, size, gdk)

    def get_flame(self, size=None, gdk=False):
        """
        Grabs the flame graphic, so it's clear when viewing maps.  I provide my own
        image here instead of using the game's because the file bundled with the game
        doesn't have transparency information, and I don't feel like doing a conversion.
        """
        if (self.flamecache is None):
            with open(os.path.join(self.datadir, 'torch_single.png'), 'rb') as df:
                flamedata = df.read()
            self.flamecache = B1GfxEntCache(flamedata, 1, 1)
        if (size is None):
            size = self.tile_width
        return self.flamecache.getimg(1, int(size * self.flamecache.size_scale), gdk)

    def get_entity(self, entnum, direction, size=None, gdk=False):
        entity = self.eschalondata.get_entity(entnum)
        if not entity:
            return None
        entnum = entity.gfxfile
        if (entnum not in self.entcache):
            filename = 'mo%d.png' % (entnum)
            if (entnum in self.restrict_ents):
                self.entcache[entnum] = B1GfxEntCache(
                    self.readfile(filename), 2, 1)
            else:
                self.entcache[entnum] = B1GfxEntCache(self.readfile(filename))
        cache = self.entcache[entnum]
        if (size is None):
            size = self.tile_width
        return cache.getimg(direction, int(size * cache.size_scale), gdk)

    def get_avatar(self, avatarnum):
        if avatarnum < 0 or avatarnum > 7:
            return None
        if avatarnum not in self.avatarcache:
            if avatarnum == 7:
                if os.path.exists(os.path.join(self.eschalondata.gamedir, 'mypic.png')):
                    self.avatarcache[avatarnum] = GdkPixbuf.Pixbuf.new_from_file(
                        os.path.join(self.eschalondata.gamedir, 'mypic.png'))
                else:
                    return None
            else:
                self.avatarcache[avatarnum] = GfxCache(
                    self.readfile('{}.png'.format(avatarnum)), 60, 60, 1).pixbuf
        return self.avatarcache[avatarnum]


class B2Gfx(Gfx):
    """
    Graphics structure for Book 2
    """

    book = 2
    zip = None
    wall_types = {}
    wall_gfx_group = {}
    tilebuf_mult = 1.5
    item_dim = 50
    item_cols = 10
    item_rows = 10
    tile_width = 64
    tile_height = 32
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

    GFX_SET_OBJ = 1
    GFX_SET_WALL = 2
    GFX_SET_TREE = 3

    def __init__(self, datadir, eschalondata):

        # Wall graphic groups
        for i in range(251):
            self.wall_gfx_group[i] = self.GFX_SET_OBJ
        for i in range(251, 256):
            self.wall_gfx_group[i] = self.GFX_SET_TREE
        for i in range(256, 513):
            self.wall_gfx_group[i] = self.GFX_SET_WALL

        # Wall object types
        for i in (list(range(251)) + list(range(266, 272)) + list(range(282, 286)) +
                  list(range(314, 320)) + list(range(330, 336)) + list(range(346, 352)) +
                  list(range(364, 368)) + list(range(378, 384)) + list(range(394, 402)) +
                  list(range(403, 513))):
            self.wall_types[i] = self.TYPE_OBJ
        for i in range(251, 256):
            self.wall_types[i] = self.TYPE_TREE
        for i in (list(range(256, 266)) + list(range(272, 282)) + list(range(286, 314)) +
                  list(range(320, 330)) + list(range(336, 346)) + list(range(352, 364)) +
                  list(range(368, 378)) + list(range(384, 394)) + [402]):
            self.wall_types[i] = self.TYPE_WALL

        # Book 2 specific caches
        self.treecache = [None, None, None]
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

        # Item category graphic file lookups
        self.itemcategory_gfxcache_idx = {}
        for num in range(50):
            self.itemcategory_gfxcache_idx[num] = 'misc'
        for num in range(1, 3):
            self.itemcategory_gfxcache_idx[num] = 'weapons'
        for num in range(3, 11):
            self.itemcategory_gfxcache_idx[num] = 'armor'
        for num in list(range(11, 16)) + [17]:
            self.itemcategory_gfxcache_idx[num] = 'magic'

        # Finally call the parent constructor
        super(B2Gfx, self).__init__(datadir, eschalondata)

    def item_overlayfunc(self, surface, width, height, cols, category):
        """
        In Book 2/3, the Weapon and Armor graphics don't have a background,
        which looks a little odd in the GUI.  So we construct them based on
        the given elements in the data dir.
        """

        # First load in the background and its frame
        frame = self.eschalondata.readfile('icon_frame.png')
        background = self.eschalondata.readfile(
            '%s_icon_blank.png' % (category))
        framesurf = cairo.ImageSurface.create_from_png(
            io.BytesIO(frame))
        backsurf = cairo.ImageSurface.create_from_png(
            io.BytesIO(background))

        # Now create a new surface and tile the background over the whole thing
        newsurf = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, surface.get_width(), surface.get_height())
        newctx = cairo.Context(newsurf)
        rows = int(surface.get_height() // height)
        for row in range(rows):
            for col in range(cols):
                newctx.set_source_surface(backsurf, col * width, row * height)
                newctx.rectangle(col * width, row * height, width, height)
                newctx.paint()

        # Overlay our passed-in surface on top
        newctx.set_source_surface(surface, 0, 0)
        newctx.rectangle(0, 0, surface.get_width(), surface.get_height())
        newctx.paint()

        # Now tile the frame on top of every item
        for row in range(rows):
            for col in range(cols):
                newctx.set_source_surface(framesurf, col * width, row * height)
                newctx.rectangle(col * width, row * height, width, height)
                newctx.paint()

        return newsurf

    def item_overlayfunc_armor(self, surface, width, height, cols):
        return self.item_overlayfunc(surface, width, height, cols, 'armor')

    def item_overlayfunc_weapon(self, surface, width, height, cols):
        return self.item_overlayfunc(surface, width, height, cols, 'weapon')

    def get_item(self, item, size=None, gdk=True):
        if item.category not in self.itemcategory_gfxcache_idx:
            idx = 'misc'
        else:
            idx = self.itemcategory_gfxcache_idx[item.category]
        if (self.itemcache[idx] is None):
            self.itemcache[idx] = GfxCache(self.eschalondata.readfile(
                '%s_sheet.png' % (idx)), 50, 50, 10, self.itemcache_overlayfunc[idx])
        return self.itemcache[idx].getimg(item.pictureid + 1, size, gdk)

    def get_floor(self, floornum, size=None, gdk=False):
        if (floornum == 0):
            return None
        if (self.floorcache is None):
            self.floorcache = GfxCache(
                self.eschalondata.readfile('iso_base.png'), 64, 32, 8)
        return self.floorcache.getimg(floornum, size, gdk)

    def get_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.decalcache is None):
            self.decalcache = GfxCache(self.eschalondata.readfile(
                'iso_basedecals.png'), 64, 32, 16)
        return self.decalcache.getimg(decalnum, size, gdk)

    # Returns a tuple, first item is the surface, second is the extra height to add while drawing
    def get_object(self, objnum, size=None, gdk=False, treeset=0):
        if (objnum == 0):
            return (None, 0, 0)
        try:
            walltype = self.wall_gfx_group[objnum]
        except KeyError:
            return (None, 0, 0)
        if (walltype == self.GFX_SET_OBJ):
            if (self.objcache1 is None):
                self.objcache1 = GfxCache(
                    self.eschalondata.readfile('iso_obj.png'), 64, 64, 16)
            return (self.objcache1.getimg(objnum, size, gdk), 1, 0)
        elif (walltype == self.GFX_SET_WALL):
            if (self.objcache2 is None):
                self.objcache2 = GfxCache(
                    self.eschalondata.readfile('iso_walls.png'), 64, 96, 16)
            return (self.objcache2.getimg(objnum - 255, size, gdk), 2, 0)
        elif (walltype == self.GFX_SET_TREE):
            if (self.treecache[treeset] is None):
                self.treecache[treeset] = GfxCache(self.eschalondata.readfile(
                    'iso_trees%d.png' % (treeset)), 96, 160, 5)
            if (objnum in self.treemap):
                # note the size difference for Book 2 trees (50% wider)
                if not size:
                    size = self.tile_width
                offset = -int(size / 4)
                size = int(size * 1.5)
                return (self.treecache[treeset].getimg(self.treemap[objnum], size, gdk), 4, offset)
            else:
                return (None, 4, 0)

    def get_object_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.objdecalcache is None):
            self.objdecalcache = GfxCache(
                self.eschalondata.readfile('iso_objdecals.png'), 64, 96, 16)
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
            # The torch image came from Book 1 and is scaled to 52 pixels, not
            # 64, which is why we're passing that in here.  I figure there's not
            # much point to having a separate Book 1 and Book 2 flame graphic.
            self.flamecache = SingleImageGfxCache(flamedata, 52.0)
        if (size is None):
            size = self.tile_width
        return self.flamecache.getimg(1, int(size * self.flamecache.size_scale), gdk)

    def get_zapper(self, size=None, gdk=False):
        """
        Grabs a zapper image.
        """
        if (self.zappercache is None):
            df = open(os.path.join(self.datadir, 'zappy_single.png'), 'rb')
            zapperdata = df.read()
            df.close()
            self.zappercache = SingleImageGfxCache(zapperdata)
        if (size is None):
            size = self.tile_width
        return self.zappercache.getimg(1, int(size * self.zappercache.size_scale), gdk)

    def get_huge_gfx(self, filename, size=None, gdk=False):
        """
        Grabs an arbitrary graphic file from our pool (used for the "huge" graphics like Hammerlorne,
        Corsair ships, etc, in Book 2/3)
        """
        if filename not in self.hugegfxcache:
            if (filename.find('/') != -1 or filename.find('..') != -1 or filename.find('\\') != -1):
                return None
            try:
                self.hugegfxcache[filename] = SingleImageGfxCache(
                    self.eschalondata.readfile(filename))
            except LoadException:
                return None
        if (size is None):
            size = self.tile_width
        return self.hugegfxcache[filename].getimg(1, int(size * self.hugegfxcache[filename].size_scale), gdk)

    def get_entity(self, entnum, direction, size=None, gdk=False):
        ent = self.eschalondata.get_entity(entnum)
        if not ent:
            return None
        if (entnum not in self.entcache):
            filename = ent.gfxfile
            self.entcache[entnum] = B23GfxEntCache(
                ent, self.eschalondata.readfile(filename))
        cache = self.entcache[entnum]
        if (size is None):
            size = self.tile_width
        return cache.getimg(direction, int(size * cache.size_scale), gdk)

    def get_avatar(self, avatarnum):
        if avatarnum == 0xFFFFFFFF or (0 <= avatarnum <= 12):
            if avatarnum not in self.avatarcache:
                if avatarnum == 0xFFFFFFFF:
                    if os.path.exists(os.path.join(self.eschalondata.gamedir, 'mypic.png')):
                        self.avatarcache[avatarnum] = GdkPixbuf.Pixbuf.new_from_file(
                            os.path.join(self.eschalondata.gamedir, 'mypic.png'))
                    else:
                        return None
                else:
                    self.avatarcache[avatarnum] = GfxCache(self.eschalondata.readfile(
                        'port{}.png'.format(avatarnum)), 64, 64, 1).pixbuf
            return self.avatarcache[avatarnum]
        else:
            return None


class B3Gfx(B2Gfx):
    """
    Graphics structure for Book 3
    """

    book = 3
    obj_a_rows = 11

    def __init__(self, datadir, eschalondata):
        # Call the B2 constructor first, then override for unique Book III
        # stuff
        super(B3Gfx, self).__init__(datadir, eschalondata)

        # Book III has four tree sets
        self.treecache = [None, None, None, None]
