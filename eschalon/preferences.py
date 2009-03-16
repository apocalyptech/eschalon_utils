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

import sys
import os
import os.path
import ConfigParser
from eschalonb1 import app_name

# TODO: Error handling on load() and save()

class Prefs(object):

    def __init__(self):
        self.cp = ConfigParser.ConfigParser()
        if 'win32' in sys.platform:
            self.platform = 'win32'
            self.default = self.windows_default
            self.filename = self.windows_prefsfile()
        elif 'cygwin' in sys.platform:
            self.platform = 'cygwin'
            self.default = self.no_default
            self.filename = self.no_prefsfile()
        elif 'darwin' in sys.platform:
            self.platform = 'darwin'
            self.default = self.no_default
            self.filename = self.no_prefsfile()
        else:
            # Assume linux
            self.platform = 'linux'
            self.default = self.linux_default
            self.filename = self.linux_prefsfile()

        # Initialize our defaults and load, if we can
        self.set_defaults()
        if (not self.load()):
            # Write out our prefs if one didn't exist
            self.save()

    def set_defaults(self):
        # We're loading gamedir first because sometimes Windows will have its
        # savegames stored in there, so it'd be useful to know that first
        for vars in [('paths', 'gamedir'), ('paths', 'savegames')]:
            self.set_str(vars[0], vars[1], self.default(vars[0], vars[1]))

    def load(self):
        if (self.filename is not None and os.path.isfile(self.filename)):
            self.cp.read(self.filename)
            return True
        else:
            return False

    def save(self):
        if (self.filename is not None):
            df = open(self.filename, 'w')
            self.cp.write(df)
            df.close()

    def set_str(self, cat, name, val):
        if (not self.cp.has_section(cat)):
            self.cp.add_section(cat)
        return self.cp.set(cat, name, val)

    def get_str(self, cat, name):
        return self.cp.get(cat, name)

    def no_prefsfile(self):
        """ Fallback when we don't know anything about the platform. """
        return None

    def no_default(self, cat, name):
        """ Fallback when we don't know anything about the platform. """
        return None

    def linux_prefsfile(self):
        """ Default prefsfile on Linux """
        return os.path.join(os.path.expanduser('~'), '.eschalon_b1_utils_rc')

    def linux_default(self, cat, name):
        """ Default values on Linux """
        if (cat == 'paths'):
            if (name == 'savegames'):
                path = os.path.join(os.path.expanduser('~'), '.eschalon_b1_saved_games')
                if (not os.path.isdir(path)):
                    path = os.path.join(os.path.expanduser('~'), 'eschalon_b1_saved_games')
                return path
            elif (name == 'gamedir'):
                for dir in [ '/usr/games', '/opt', '/opt/games', '/usr/share/games', '/usr/local/games' ]:
                    fulldir = os.path.join(dir, 'eschalon_book_1')
                    if (os.path.isfile(os.path.join(fulldir, 'gfx.pak'))):
                        return fulldir
                # If nothing found, just return our last-created fulldir
                return fulldir
        return None

    def windows_prefsfile(self):
        """ Default prefsfile on Windows """
        # TODO: Or should it go into "Local Settings\Application Data\"?  Or "My Documents"?
        appdir = os.path.join(os.path.expanduser('~'), 'Application Data')
        if (not os.path.isdir(appdir)):
            os.mkdir(appdir)
        prefsdir = os.path.join(appdir, app_name)
        if (not os.path.isdir(prefsdir)):
            os.mkdir(prefsdir)
        return os.path.join(prefsdir, 'config.ini')

    def windows_default(self, cat, name):
        """ Default values on Windows """
        # Registry keys are in: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Eschalon Book I_is1
        #  * specifically the key "InstallLocation" could help ("Inno Setup: App Path" is the same)
        if (cat == 'paths'):
            if (name == 'savegames'):
                for dir in [ self.get_str('paths', 'gamedir'), os.path.join(os.path.expanduser('~'), 'My Documents') ]:
                    testdir = os.path.join(dir, 'Eschalon Book 1 Saved Games')
                    if (os.path.isdir(testdir)):
                        return testdir
                # ... and if we get here, just return our most recent testdir, anyway
                return testdir
            elif (name == 'gamedir'):
                for dir in [ 'C:\\Games', 'C:\\Program Files' ]:
                    testdir = os.path.join(dir, 'Eschalon Book I')
                    if (os.path.isfile(os.path.join(testdir, 'gfx.pak'))):
                        return testdir
                # TODO: Inspect the registry above and return that instead.  For
                # now, return our most recent testdir instead.
                return testdir
        return None
