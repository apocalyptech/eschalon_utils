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

import sys
import zlib
from eschalon.savefile import Savefile, LoadException
from struct import unpack


class PakIndex(object):
    """ A class to hold information on an individual file in the pak. """

    def __init__(self, data):
        (self.size_compressed,
         self.abs_index,
         self.size_real,
         self.unknowni1) = unpack('<IIII', data[:16])
        self.filename = data[16:]
        self.filename = self.filename[:self.filename.index("\x00")]


df = Savefile(sys.argv[1])

df.open_r()
header = df.read(4)
if (header != '!PAK'):
    df.close()
    raise LoadException('Invalid PAK header')

# Initial Values
unknownh1 = df.readshort()
unknownh2 = df.readshort()
numfiles = df.readint()
compressed_idx_size = df.readint()
unknowni1 = df.readint()

# Now load in the index
decobj = zlib.decompressobj()
indexdata = decobj.decompress(df.read())
zeroindex = df.tell() - len(decobj.unused_data)
decobj = None
fileindex = {}
for i in range(numfiles):
    index = PakIndex(indexdata[:272])
    indexdata = indexdata[272:]
    fileindex[index.filename] = index

for filename in list(fileindex.keys()):
    index = fileindex[filename]
    print(filename)
    df.seek(zeroindex + index.abs_index)
    # On Windows, we need to specify bufsize or memory gets clobbered
    filedata = zlib.decompress(
        df.read(index.size_compressed), 15, index.size_real)

for filename in fileindex.keys():
  index = fileindex[filename]
  print (filename)
  df.seek(zeroindex + index.abs_index)
  # On Windows, we need to specify bufsize or memory gets clobbered
  filedata = zlib.decompress(
    df.read(index.size_compressed), 15, index.size_real)
  with open(filename, 'wb') as f:
      f.write(filedata)