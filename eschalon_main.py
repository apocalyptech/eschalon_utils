#!/usr/bin/env python2
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

import sys

import argparse

from eschalon.mapgui import MapGUI
from eschalon.maincli import MainCLI
from eschalon.preferences import Prefs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action="append", type=str,
                        choices=['all', 'stats', 'avatar', 'magic', 'equip', 'inv']
                        )
    parser.add_argument("-u", "--unknowns", action="store_true")

    char_manip_group = parser.add_argument_group(title="automated changes", description="sgkljfld")
    char_manip_group.add_argument("--set-gold", type=int)
    char_manip_group.add_argument("--set-mana-max", type=int)
    char_manip_group.add_argument("--set-mana-cur", type=int)
    char_manip_group.add_argument("--set-hp-max", type=int)
    char_manip_group.add_argument("--set-hp-cur", type=int)
    char_manip_group.add_argument("--rm-desease", action="store_true")

    # TODO: more advanced CLI validation checks
    parser.add_argument("filename", type=str, action='append')
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--map", action="store_true")
    parser.add_argument("--book", type=int, choices=[1, 2, 3], required=True)

    args = parser.parse_args()

    if args.gui:
        # We're waiting until now to import, so people just using CLI don't need
        # PyGTK installed, etc).  Not that this program follows PEP8-recommended
        # practices anyway, but I *am* aware that doing this is discouraged.
        from eschalon.maingui import MainGUI
        prog = MainGUI(args, Prefs(), args.book)
    elif args.map:
        prog = MapGUI(args.filename, Prefs(), args.book)
    else:
        prog = MainCLI(args, Prefs(), args.book)

    return prog.run()


if __name__ == '__main__':
    sys.exit(main())
