#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2017 CJ Kucera, Elliot Kendall
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

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import sys
from eschalon.mapgui import MapGUI
from eschalon.preferences import Prefs


def main():
    parser = argparse.ArgumentParser(description=""
                                                 "To load a map automatically without going through the GUI dialog,"
                                                 "specify the location of the file named with a '.map' extension."
                                                 "",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--book", type=int, required=True, choices=[1,2,3])
    parser.add_argument("--filename", type=str, action='append')

    args = parser.parse_args()

    prog = MapGUI(args.filename, Prefs(), args.book)
    return prog.run()


if __name__ == '__main__':
    sys.exit(main())
