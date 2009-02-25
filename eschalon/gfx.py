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

import os
import gtk
import math
import zlib
import cairo
from struct import unpack
from eschalonb1.savefile import Savefile, LoadException

class GfxCairoHelper:
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

class GfxGDKHelper:
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

class GfxCache:
    """ A class to hold graphic data, with resizing abilities and the like. """

    def __init__(self, pngdata, width, height, cols):
        self.surface = cairo.ImageSurface.create_from_png(GfxCairoHelper(pngdata))
        self.width = width
        self.height = height
        self.cols = cols
        self.cache = {}

    def getimg(self, number, sizex=None):
        """ Grab an image from the cache, as a Cairo surface. """
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

class PakIndex:
    """ A class to hold information on an individual file in the pak. """

    def __init__(self, data):
        (self.size_compressed,
                self.abs_index,
                self.size_real,
                self.unknowni1) = unpack('<IIII', data[:16])
        self.filename = data[16:]
        self.filename = self.filename[:self.filename.index("\x00")]

class Gfx:
    """ A class to hold graphics data. """

    def __init__(self, prefs):
        """ A fresh object with no data. """

        self.prefs = prefs
        self.pakloc = os.path.join(self.prefs.get_str('paths', 'gamedir'), 'gfx.pak')
        self.df = Savefile(self.pakloc)

        self.unknownh1 = -1
        self.unknownh2 = -1
        self.numfiles = -1
        self.unknowni1 = -1
        self.unknowni2 = -1
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
        self.unknowni1 = df.readint()
        self.unknowni2 = df.readint()

        # Some graphic-specific indexes/flags
        self.itemcache = None
        self.itemcache_gdk = {}
        self.floorcache = None
        self.decalcache = None
        self.objcache1 = None
        self.objcache2 = None
        self.objcache3 = None
        self.objcache4 = None
        self.objdecalcache = None
        self.avatarcache = {}
        self.avatarcache_gdk = {}

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
                filedata = zlib.decompress(self.df.read(self.fileindex[filename].size_compressed))
                self.df.close()
                return filedata
            else:
                raise LoadException('Filename %s not found in archive' % (filename))
        else:
            raise LoadException('PAK Index has not been loaded')

    def get_item(self, itemnum, size=None):
        if (self.itemcache is None):
            self.itemcache = GfxCache(self.readfile('items_mastersheet.png'), 42, 42, 10)
        key = "%d-%s"%(itemnum, size)
        if (key not in self.itemcache_gdk):
            self.itemcache_gdk[key] = self.surface_to_pixbuf(self.itemcache.getimg(itemnum+1, size))
        return self.itemcache_gdk[key]

    def get_floor(self, floornum, size=None):
        if (floornum == 0):
            return None
        if (self.floorcache is None):
            self.floorcache = GfxCache(self.readfile('iso_tileset_base.png'), 52, 26, 6)
        return self.floorcache.getimg(floornum, size)

    def get_decal(self, decalnum, size=None):
        if (decalnum == 0):
            return None
        if (self.decalcache is None):
            self.decalcache = GfxCache(self.readfile('iso_tileset_base_decals.png'), 52, 26, 6)
        return self.decalcache.getimg(decalnum, size)

    # Returns a tuple, first item is the surface, second is the extra height to add while drawing
    def get_object(self, objnum, size=None):
        if (objnum == 0):
            return (None, 0)
        if (objnum < 101):
            if (self.objcache1 is None):
                self.objcache1 = GfxCache(self.readfile('iso_tileset_obj_a.png'), 52, 52, 6)
            return (self.objcache1.getimg(objnum, size), 1)
        elif (objnum < 161):
            if (self.objcache2 is None):
                self.objcache2 = GfxCache(self.readfile('iso_tileset_obj_b.png'), 52, 78, 6)
            return (self.objcache2.getimg(objnum-100, size), 2)
        elif (objnum < 251):
            if (self.objcache3 is None):
                self.objcache3 = GfxCache(self.readfile('iso_tileset_obj_c.png'), 52, 78, 6)
            return (self.objcache3.getimg(objnum-160, size), 2)
        else:
            if (self.objcache4 is None):
                self.objcache4 = GfxCache(self.readfile('iso_trees.png'), 52, 130, 5)
            return (self.objcache4.getimg(self.treemap[objnum], size), 4)

    def get_object_decal(self, decalnum, size=None):
        if (decalnum == 0):
            return None
        if (self.objdecalcache is None):
            self.objdecalcache = GfxCache(self.readfile('iso_tileset_obj_decals.png'), 52, 78, 6)
        return self.objdecalcache.getimg(decalnum, size)

    def get_avatar(self, avatarnum):
        if (avatarnum < 0 or avatarnum > 7):
            return None
        if (avatarnum not in self.avatarcache):
            if (avatarnum == 7):
                if (os.path.exists(os.path.join(self.prefs.get_str('paths', 'gamedir'), 'mypic.png'))):
                    self.avatarcache[avatarnum] = cairo.ImageSurface.create_from_png(os.path.join(self.prefs.get_str('paths', 'gamedir'), 'mypic.png'))
                else:
                    return None
            else:
                self.avatarcache[avatarnum] = GfxCache(self.readfile('%d.png' % (avatarnum)), 60, 60, 1).surface
            self.avatarcache_gdk[avatarnum] = self.surface_to_pixbuf(self.avatarcache[avatarnum])
        return self.avatarcache_gdk[avatarnum]

    def surface_to_pixbuf(self, surface):
        gdkhelper = GfxGDKHelper()
        surface.write_to_png(gdkhelper)
        loader = gtk.gdk.PixbufLoader()
        loader.write(gdkhelper.getdata())
        loader.close()
        return loader.get_pixbuf()
