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
import argparse
import logging
import sys


import coloredlogs
import verboselogs

from eschalon.preferences import Prefs

LOG = logging.getLogger(__name__)


def parse_args(args):
    """
    Pull out argument parsing into a seperate function.
    It turns out this is a sufficiently complicated task that it should be tested.
    :param args:
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action="append", type=str,
                        choices=['all', 'stats', 'avatar',
                                 'magic', 'equip', 'inv']
                        )
    parser.add_argument("-u", "--unknowns", action="store_true")

    char_manip_group = parser.add_argument_group(title="automated changes",
                                                 description="Sets specific charater attributes")
    char_manip_group.add_argument("--set-gold", type=int)
    char_manip_group.add_argument("--set-mana-max", type=int)
    char_manip_group.add_argument("--set-mana-cur", type=int)
    char_manip_group.add_argument("--set-hp-max", type=int)
    char_manip_group.add_argument("--set-hp-cur", type=int)
    char_manip_group.add_argument("--rm-disease", action="store_true")
    char_manip_group.add_argument("--reset-hunger", action="store_true")

    parser.add_argument("filename", type=str, nargs='?')
    which_gui = parser.add_mutually_exclusive_group()
    which_gui.add_argument("--char", action="store_true")
    which_gui.add_argument("--map", action="store_true")

    parser.add_argument("--book", type=int, choices=[1, 2, 3])

    parser.add_argument('--log',
                        dest='logLevel',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                 'CRITICAL', 'VERBOSE', 'SPAM', 'SUCCESS', 'NOTICE'],
                        help='Set the logging level',
                        default='INFO',
                        )

    args = parser.parse_args(args)

    manip_options_set = any([args.set_gold, args.unknowns, args.list, args.set_mana_max, args.set_mana_cur,
                             args.set_hp_max, args.set_hp_cur, args.rm_disease, args.reset_hunger])

    if not args.map and args.filename is None:
        args.char = True

    # Validation some odd combinations. Annoyingly argparse doesn't make this easier.
    if args.book == 1 and args.reset_hunger:
        parser.error("Resetting hunger/thirst only applies to book II and III")
    if manip_options_set and args.filename is None:
        parser.error("Can only manipulate values on a file")
    if any([args.char, args.map]):
        if manip_options_set:
            parser.error(
                "GUI can't be combined with listing/manipulation options")
    else:
        if args.filename is not None and not manip_options_set:
            parser.error("Select a mode operation (--char or --map)")

    if args.book is None and args.filename is not None:
        parser.error("Book version must be selected with filename")

    return args


def main():

    args = parse_args(sys.argv[1:])
    coloredlogs.install(milliseconds=True, level=args.logLevel)
    LOG.verbose("Logging Started")

    # We're waiting until now to import, so people just using CLI don't need
    # PyGTK installed, etc). I *am* aware that doing this is discouraged.
    if args.book is None and args.filename is None:
        import eschalon.bookchooser
        prog = eschalon.bookchooser.BookChooser()
    elif args.char:
        from eschalon.maingui import MainGUI
        prog = MainGUI(args.filename, Prefs(), args.book)
    elif args.map:
        from eschalon.mapgui import MapGUI
        prog = MapGUI(args.filename, Prefs(), args.book)
    else:
        from eschalon.maincli import MainCLI
        prog = MainCLI(args.filename, Prefs(), args.book, args)

    return prog.run()


if __name__ == '__main__':
    sys.exit(main())
