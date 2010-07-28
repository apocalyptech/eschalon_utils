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

import getopt, sys
from eschalon.map import Map
from eschalon.mapcli import MapCLI
from eschalon.preferences import Prefs

def usage(full=False):
    #progname = sys.argv[0]
    progname = 'eschalon_b1_map.py'
    print
    print "To launch the GUI:"
    print "\t%s [<mapfile>]" % (progname)
    print
    print "To list map attributes on the console:"
    print "\t%s -l [-s <squares|objects|txtmap>] [-u] <mapfile>" % (progname)
    print "\t%s --list [--show=<squares|...>] [--unknowns] <mapfile>" % (progname)
    print
    if (full):
        print "Wherever <mapfile> appears in the above, you should specify the"
        print "location of the file named with a '.map' extension.  This utility"
        print "can load both maps that are inside your savegame folder, and the"
        print "stock maps in Eschalon Book 1's 'data' directory."
        print
        print "By default, the application will launch the GUI.  Note that"
        print "specifying a map file is optional when you're launching"
        print "the GUI, but required when using any of the other commandline"
        print "options."
        print
        print "For a textual representation of the map instead, use -l or"
        print "--list.  Note that the commandline options aren't terribly useful,"
        print "but you'll at least get some information out of them."
        print
        print "By default, the --list option will only show the basic map"
        print "information.  To get a text listing of the attributes of every"
        print "single square on the map (you'll probabably want to redirect this"
        print "to a file, since there are 20,000 squares in an Eschalon map,"
        print "though the utility will skip empty squares), you would use:"
        print
        print "\t%s -l -s squares <mapfile>" % (progname)
        print "\tor"
        print "\t%s --list --show=squares <mapfile>" % (progname)
        print
        print "If you wanted a listing of all the objects in the map, specify"
        print "'objects' instead of 'squares'."
        print
        print "When being shown the listing, specify -u or --unknowns to"
        print "also show unknown data from the map file."
        print
        print "I left in the first visual feature I implemented, which is a text"
        print "view of the map, which'll simply draw an asterisk where there's"
        print "a wall, and blank otherwise.  You'll need a really tiny console"
        print "font and a largeish console window for this to make sense.  On my"
        print "system's xterm, the 'tiny' font setting seemed about good enough."
        print "This option's even less useful than the other console options, of"
        print "course, but I'll leave it in regardless.  To show the text-based"
        print "map:"
        print
        print "\t%s -l -s txtmap <mapfile>" % (progname)
        print "\tor"
        print "\t%s --list --show=txtmap <mapfile>" % (progname)
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
            'gui': True,
            'list': False,
            'listoptions' : {
                'all': False,
                'squares': False,
                'objects': False,
                'txtmap': False
                },
            'unknowns': False,
            'filename' : None
            }

    # Parse the args
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:],
                'hls:u',
                ['help',
                 'list',
                 'show=',
                 'unknowns'])
    except getopt.GetoptError, err:
        print str(err)
        usage()

    # now check to see if they're proper
    for o, a in opts:
        if (o in ('-h', '--help')):
            usage(True)
        elif (o in ('-l', '--list')):
            options['gui'] = False
            options['list'] = True
        elif (o in ('-s', '--show')):
            if (a == 'squares'):
                options['listoptions']['squares'] = True
            elif (a == 'objects'):
                options['listoptions']['objects'] = True
            elif (a == 'txtmap'):
                options['listoptions']['txtmap'] = True
            else:
                usage()
        elif (o in ('-u', '--unknowns')):
            options['unknowns'] = True
        else:
            assert False, 'unhandled option'

    # Set our filename, if we have it
    if (len(args) > 0):
        options['filename'] = args[0]
        # TODO: this was here to support me doing mass graphic exports.
        # remove it?
        options['filenames'] = args

    # Make sure we have a filename still
    if (not options['gui'] and options['filename'] == None):
        print "A filename is required"
        usage()
    
    # Now load up the appropriate class
    if (options['gui']):
        # We're waiting until now to import, so people just using CLI don't need
        # PyGTK installed, etc).  Not that this program follows PEP8-recommended
        # practices anyway, but I *am* aware that doing this is discouraged.
        from eschalon.mapgui import MapGUI
        prog = MapGUI(options, Prefs(), 2)
    else:
        prog = MapCLI(options, Prefs(), 2)

    # ... and run it
    return prog.run()

if __name__ == '__main__':
    sys.exit(main())
