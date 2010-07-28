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

import sys
import os
import os.path
import ConfigParser
from eschalon import app_name

# Load windows registry, if we can
try:
    import _winreg
except ImportError, e:
    pass

# TODO: Error handling on load() and save()

class Prefs(object):

    def __init__(self):
        self.cp = ConfigParser.ConfigParser()
        if 'win32' in sys.platform:
            self.platform = 'win32'
            self.default = self.win32_default
            self.filename = self.win32_prefsfile()
        elif 'cygwin' in sys.platform:
            self.platform = 'cygwin'
            self.default = self.no_default
            self.filename = self.no_prefsfile()
        elif 'darwin' in sys.platform:
            self.platform = 'darwin'
            self.default = self.darwin_default
            self.filename = self.darwin_prefsfile()
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
        for vars in [('paths', 'gamedir'), ('paths', 'gamedir_b2'), ('paths', 'savegames'), ('paths', 'savegames_b2')]:
            self.set_str(vars[0], vars[1], self.default(vars[0], vars[1]))
        for vars in [('mapgui', 'default_zoom')]:
            self.set_int(vars[0], vars[1], self.default(vars[0], vars[1]))
        for vars in [('mapgui', 'warn_global_map'), ('mapgui', 'warn_slow_zip')]:
            self.set_bool(vars[0], vars[1], self.default(vars[0], vars[1]))

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

    def set_int(self, cat, name, val):
        if (not self.cp.has_section(cat)):
            self.cp.add_section(cat)
        return self.cp.set(cat, name, str(val))

    def get_int(self, cat, name):
        return self.cp.getint(cat, name)

    def set_bool(self, cat, name, val):
        if (not self.cp.has_section(cat)):
            self.cp.add_section(cat)
        if val:
            val = 'True'
        else:
            val = 'False'
        return self.cp.set(cat, name, val)

    def get_bool(self, cat, name):
        return self.cp.getboolean(cat, name)

    def global_default(self, cat, name):
        """ Defaults which are global, regardless of platform. """
        if (cat == 'mapgui'):
            if (name == 'default_zoom'):
                return 4
            elif (name == 'warn_global_map'):
                return 'True'
            elif (name == 'warn_slow_zip'):
                return 'True'
        elif (cat == 'paths'):
            if (name == 'gamedir_b2'):
                return ''
        return None

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
            elif (name == 'savegames_b2'):
                return os.path.join(os.path.expanduser('~'), '.basilisk_games', 'book2_saved_games')
            elif (name == 'gamedir'):
                for dir in [ '/usr/games', '/opt', '/opt/games', '/usr/share/games', '/usr/local/games' ]:
                    fulldir = os.path.join(dir, 'eschalon_book_1')
                    if (os.path.isfile(os.path.join(fulldir, 'gfx.pak'))):
                        return fulldir
                # If nothing found, just return our last-created fulldir
                return fulldir
        return self.global_default(cat, name)

    def darwin_prefsfile(self):
        """ Default prefsfile on Darwin """
        prefdir = os.path.join(os.path.expanduser('~'), 'Library', 'Preferences', app_name)
        if (not os.path.isdir(prefdir)):
            os.mkdir(prefdir)
        return os.path.join(prefdir, 'config.ini')

    def darwin_default(self, cat, name):
        """ Default values on Darwin """
        # TODO: These are completely untested - the gamedir and savegames_b2 in particular are
        # both total guesses on my part.
        if (cat == 'paths'):
            if (name == 'savegames'):
                return os.path.join(os.path.expanduser('~'), 'Documents', 'Eschalon Book 1 Saved Games')
            elif (name == 'savegames'):
                return os.path.join(os.path.expanduser('~'), 'Documents', 'Eschalon Book 2 Saved Games')
            elif (name == 'gamedir'):
                return '/Applications/Eschalon Book I.app'
        return self.global_default(cat, name)

    def win32_prefsfile_final(self, path):
        """ Given a path, spit out our prefsfile from that root. """
        dir = os.path.join(path, app_name)
        if (not os.path.isdir(dir)):
            os.mkdir(dir)
        return os.path.join(dir, 'config.ini')

    # Should probably review and conform to http://msdn.microsoft.com/en-us/library/ms811696.aspx
    def win32_prefsfile(self):
        """ Default prefsfile on Windows """

        # First, where it Should be
        appdir = os.path.join(os.path.expanduser('~'), 'Local Settings', 'Application Data')
        if (os.path.isdir(appdir)):
            return self.win32_prefsfile_final(appdir)

        # If "Local Settings" isn't available for some reason, just put it in Application Data
        appdir = os.path.join(os.path.expanduser('~'), 'Application Data')
        if (os.path.isdir(appdir)):
            return self.win32_prefsfile_final(appdir)

        # When logged in as Administrator on some boxes, expanduser() doesn't work
        # properly (at least on win2k, on Python 2.5).  Check USERPROFILE and try from there.
        if ('USERPROFILE' in os.environ):
            if (os.path.isdir(os.environ['USERPROFILE'])):
                appdir = os.path.join(os.environ['USERPROFILE'], 'Local Settings', 'Application Data')
                if (os.path.isdir(appdir)):
                    return self.win32_prefsfile_final(appdir)

                appdir = os.path.join(os.environ['USERPROFILE'], 'Application Data')
                if (os.path.isdir(appdir)):
                    return self.win32_prefsfile_final(appdir)

        # If that didn't work out, grab our username and try that,
        if ('USERNAME' in os.environ):
            if ('HOMEDRIVE' in os.environ):
                drive = os.environ['HOMEDRIVE']
            else:
                drive = 'C:'
            constdir = os.path.join(drive, 'Documents and Settings', os.environ['USERNAME'])
            if (os.path.isdir(constdir)):
                appdir = os.path.join(constdir, 'Local Settings', 'Application Data')
                if (os.path.isdir(appdir)):
                    return self.win32_prefsfile_final(appdir)

                appdir = os.path.join(constdir, 'Application Data')
                if (os.path.isdir(appdir)):
                    return self.win32_prefsfile_final(appdir)

        # If we didn't find anything, return None - we just won't actually
        # store preferences.
        # TODO: Notification of user to get ahold of me, to figure out
        # how to do it properly on their systems.
        return None

    def win32_default(self, cat, name):
        """ Default values on Windows """
        if (cat == 'paths'):
            if (name == 'savegames'):
                for dir in [ self.get_str('paths', 'gamedir'), os.path.join(os.path.expanduser('~'), 'My Documents') ]:
                    testdir = os.path.join(dir, 'Eschalon Book 1 Saved Games')
                    if (os.path.isdir(testdir)):
                        return testdir
                # ... and if we get here, just return our most recent testdir, anyway
                return testdir
            elif (name == 'savegames_b2'):
                basedir = os.path.expanduser('~')
                savedir = os.path.join('Basilisk Games', 'Book 2 Saved Games')
                # Huzzah for flailing about!
                for dir in [ os.path.join(basedir, 'Local Settings', 'Application Data', savedir),
                        os.path.join(basedir, 'Application Data', savedir),
                        os.path.join(basedir, 'My Documents', savedir),
                        os.path.join(basedir, 'AppData', 'Roaming', savedir),
                        os.path.join(basedir, 'AppData', savedir)]:
                    if (os.path.isdir(dir)):
                        return dir
                # If we got here, um, do what?
                #return os.path.join(basedir, 'Application Data', savedir)
                return ''
            elif (name == 'gamedir'):
                for dir in [ 'C:\\Games', 'C:\\Program Files' ]:
                    testdir = os.path.join(dir, 'Eschalon Book I')
                    if (os.path.isfile(os.path.join(testdir, 'gfx.pak'))):
                        return testdir
                # If we got here, it wasn't found - check the registry.  If there
                # are any errors, just return our most recent testdir
                try:
                    wr = _winreg.OpenKey(
                        _winreg.HKEY_LOCAL_MACHINE,
                        'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Eschalon Book I_is1'
                        )
                except EnvironmentError, e:
                    return testdir

                try:
                    (val, type) = _winreg.QueryValueEx(wr, 'Inno Setup: App Path')
                    testdir = val
                except EnvironmentError, e:
                    try:
                        (val, type) = _winreg.QueryValueEx(wr, 'InstallLocation')
                        if (val[-1:] == '\\'):
                            val = val[:-1]
                        testdir = val
                    except EnvironmentError, e:
                        pass

                # Close and return what we've got
                wr.Close()
                return testdir

        return self.global_default(cat, name)
