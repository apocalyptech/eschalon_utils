#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
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

import getopt, sys
from EschalonB1 import Character, MainCLI

def processfile(filename, list=False, unknowns=False):
    """ Given a filename, load the file and display it. """

    try:
        char = Character.Character(filename)
        char.read()
        if (list):
            cli = MainCLI.MainCLI(char)
            cli.display(unknowns)
            #char.df.filename = '/tmp/cjchar'
            #char.write()
            return True
    except IOError:
        print '"' + filename + '" could not be opened.'
        return False

    # If we got here, we're launching the GUI (wait until now to import)
    from EschalonB1 import MainGUI
    app = MainGUI.MainGUI(filename, char)

    # ... and return (this will never actually happen)
    return True

def usage():
    print "Usage:"
    print
    print "\t%s [-l [-u]] <charfile>" % (sys.argv[0])
    print "\t%s [--list [--unknowns]] <charfile>" % (sys.argv[0])
    print
    print "By default, the util will launch the GUI.  For a textual"
    print "representation of the charfile, use -l or --list."
    print
    print "When being shown the listing, specify -u or --unknowns to"
    print "also show unknown data from the charfile."
    print
    print "Additionally, you may use -h or --help to view this message"
    print
    sys.exit(2)

def main(argv=None):

    # Parse the args
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], 'hlu', ['help', 'list', 'unknowns'])
    except getopt.GetoptError, err:
        print str(err)
        usage()

    # now check to see if they're proper
    list = False
    unknowns = False
    for o, a in opts:
        if (o in ('-h', '--help')):
            usage()
        elif (o in ('-l', '--list')):
            list = True
        elif (o in ('-u', '--unknowns')):
            unknowns = True
        else:
            assert False, 'unhandled option'

    # Make sure we have a filename still
    if (len(args) != 1):
        print "A filename is required"
        usage()
    
    # Now do our stuff
    return processfile(args[0], list, unknowns)

if __name__ == '__main__':
    sys.exit(main())
