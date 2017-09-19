#!/usr/bin/env python2
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

import getopt
import sys
from eschalon.map import Map
from eschalon.mapgui import MapGUI
from eschalon.preferences import Prefs


def usage(full=False):
    #progname = sys.argv[0]
    progname = 'eschalon_b2_map.py'
    print
    print "To launch the GUI:"
    print "\t%s [<mapfile>]" % (progname)
    print
    if (full):
        print "To load a map automatically without going through the GUI dialog,"
        print "specify the location of the file named with a '.map' extension."
        print
        print "Additionally, you may use -h or --help to view this message"
    else:
        print "To get a full help listing, with text descriptions of all the options:"
        print "\t%s -h" % (progname)
        print "\t%s --help" % (progname)
    print
    sys.exit(2)


def main(argv=None):

    # Argument var defaults
    options = {
        'filename': None
    }

    # Parse the args
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:],
                                   'h',
                                   ['help'])
    except getopt.GetoptError, err:
        print str(err)
        usage()

    # now check to see if they're proper
    for o, a in opts:
        if (o in ('-h', '--help')):
            usage(True)
        else:
            assert False, 'unhandled option'

    # Set our filename, if we have it
    if (len(args) > 0):
        options['filename'] = args[0]
        # TODO: this was here to support me doing mass graphic exports.
        # remove it?
        options['filenames'] = args

    # Launch
    prog = MapGUI(options, Prefs(), 2)

    # ... and run it
    return prog.run()


if __name__ == '__main__':
    sys.exit(main())
