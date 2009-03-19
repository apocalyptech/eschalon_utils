#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Character Editor
# Copyright (C) 2008, 2009 CJ Kucera
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
import gobject
from struct import unpack
from eschalonb1 import entitytable
from eschalonb1.savefile import Savefile, LoadException

class GfxCairoHelper(object):
    """
    A file-like class to load in PNG data to a Cairo surface, since
    PyCairo apparently only exports the function to load in PNG data from a file.
    """
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read(self, sizehint=-1):
        if (self.pos >= len(self.data)):
            return None
        if (sizehint < 0):
            newpos = len(self.data)
        else:
            newpos = min(self.pos + sizehint, len(self.data))
        data = self.data[self.pos:newpos]
        self.pos = newpos
        return data

class GfxGDKHelper(object):
    """
    A file-like class to read in PNG data from a Cairo surface, essentially
    to export a Cairo surface to a GDK Pixbuf.  Inefficient, of course, so
    try not to do that much.  We're doing so in the character editor, though,
    because using DrawingAreas and Cairo objects for that stuff would be
    just ludicrous.
    """
    def __init__(self):
        self.datalist = []
    def write(self, data):
        self.datalist.append(data)
    def getdata(self):
        return ''.join(self.datalist)

class GfxCache(object):
    """
    A class to hold graphic data, with resizing abilities and the like.
    It can return a Cairo surface (by default, via getimg()), or a GDK
    Pixbuf (via getimg_gdk()).  There's some code duplication between
    those two functions, which isn't ideal, but I didn't want to take the
    time to abstract the common stuff out.  So there.
    """

    def __init__(self, pngdata, width, height, cols):
        # First load the data as a Cairo surface
        self.surface = cairo.ImageSurface.create_from_png(GfxCairoHelper(pngdata))

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

class GfxEntCache(GfxCache):
    """
    A class to hold image data about entity graphics.  Mostly we're just
    overloading the constructor here, since we'd rather not hard-code what
    the various image sizes are.  Also, we can save some memory by lopping
    off much of the loaded image.
    """
    def __init__(self, pngdata, restricted=False):
        self.restricted = restricted

        # Read in the data as usual, with junk for width and height
        super(GfxEntCache, self).__init__(pngdata, -1, -1, 1)

        # ... and now that we have the image dimensions, fix that junk
        imgwidth = self.surface.get_width()
        imgheight = self.surface.get_height()
        if (restricted):
            self.width = int(imgwidth/2)
            self.height = imgheight
        else:
            self.width = int(imgwidth/15)
            self.height = int(imgheight/8)

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

    def __init__(self, prefs):
        """ A fresh object with no data. """

        self.prefs = prefs
        self.pakloc = os.path.join(self.prefs.get_str('paths', 'gamedir'), 'gfx.pak')
        self.df = Savefile(self.pakloc)

        self.restrict_ents = [50, 55, 58, 66, 67, 71]

        self.unknownh1 = -1
        self.unknownh2 = -1
        self.numfiles = -1
        self.compressed_idx_size = -1
        self.unknowni1 = -1
        self.loaded = False
        self.fileindex = {}
        self.zeroindex = -1
        self.initialread()

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

        # Some graphic-specific indexes/flags
        self.itemcache = None
        self.floorcache = None
        self.decalcache = None
        self.objcache1 = None
        self.objcache2 = None
        self.objcache3 = None
        self.objcache4 = None
        self.objdecalcache = None
        self.avatarcache = {}
        self.entcache = {}

        # wtf @ needing this
        self.treemap = {
            251: 4,
            252: 5,
            253: 1,
            254: 2,
            255: 3
            }

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

    def get_item(self, itemnum, size=None, gdk=True):
        if (self.itemcache is None):
            self.itemcache = GfxCache(self.readfile('items_mastersheet.png'), 42, 42, 10)
        return self.itemcache.getimg(itemnum+1, size, gdk)

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
    def get_object(self, objnum, size=None, gdk=False):
        if (objnum == 0):
            return (None, 0)
        if (objnum < 101):
            if (self.objcache1 is None):
                self.objcache1 = GfxCache(self.readfile('iso_tileset_obj_a.png'), 52, 52, 6)
            return (self.objcache1.getimg(objnum, size, gdk), 1)
        elif (objnum < 161):
            if (self.objcache2 is None):
                self.objcache2 = GfxCache(self.readfile('iso_tileset_obj_b.png'), 52, 78, 6)
            return (self.objcache2.getimg(objnum-100, size, gdk), 2)
        elif (objnum < 251):
            if (self.objcache3 is None):
                self.objcache3 = GfxCache(self.readfile('iso_tileset_obj_c.png'), 52, 78, 6)
            return (self.objcache3.getimg(objnum-160, size, gdk), 2)
        else:
            if (self.objcache4 is None):
                self.objcache4 = GfxCache(self.readfile('iso_trees.png'), 52, 130, 5)
            if (objnum in self.treemap):
                return (self.objcache4.getimg(self.treemap[objnum], size, gdk), 4)
            else:
                return (None, 4)

    def get_object_decal(self, decalnum, size=None, gdk=False):
        if (decalnum == 0):
            return None
        if (self.objdecalcache is None):
            self.objdecalcache = GfxCache(self.readfile('iso_tileset_obj_decals.png'), 52, 78, 6)
        return self.objdecalcache.getimg(decalnum, size, gdk)

    def get_entity(self, entnum, direction, size=None, gdk=False):
        entnum = entitytable[entnum].gfxfile
        if (entnum not in self.entcache):
            filename = 'mo%d.png' % (entnum)
            if (entnum in self.restrict_ents):
                self.entcache[entnum] = GfxEntCache(self.readfile(filename), True)
            else:
                self.entcache[entnum] = GfxEntCache(self.readfile(filename))
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

    def surface_to_pixbuf(self, surface):
        """
        Helper function to convert a Cairo surface to a GDK Pixbuf.  It's
        very slow, don't use it if you need speed.
        """
        gdkhelper = GfxGDKHelper()
        surface.write_to_png(gdkhelper)
        loader = gtk.gdk.PixbufLoader()
        loader.write(gdkhelper.getdata())
        loader.close()
        return loader.get_pixbuf()
