#!/usr/bin/python
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
        for vars in [('paths', 'gamedir'), ('paths', 'gamedir_b2'), ('paths', 'gamedir_b3'), ('paths', 'savegames'), ('paths', 'savegames_b2'), ('paths', 'savegames_b3')]:
            self.set_str(vars[0], vars[1], self.default(vars[0], vars[1]))
        for vars in [('mapgui', 'default_zoom')]:
            self.set_int(vars[0], vars[1], self.default(vars[0], vars[1]))
        for vars in [('mapgui', 'warn_slow_zip')]:
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
            elif (name == 'warn_slow_zip'):
                return 'True'
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
            elif (name == 'savegames_b3'):
                return os.path.join(os.path.expanduser('~'), '.basilisk_games', 'book3_saved_games')
            elif (name == 'gamedir'):
                for dir in [ '/usr/games', '/opt', '/opt/games', '/usr/share/games', '/usr/local/games' ]:
                    fulldir = os.path.join(dir, 'eschalon_book_1')
                    if (os.path.isdir(os.path.join(fulldir, 'packedgraphics'))):
                        return fulldir
                    if (os.path.isfile(os.path.join(fulldir, 'gfx.pak'))):
                        return fulldir
                # If nothing found, don't just assume - return a blank string.  This way it
                # could be picked up again on future runs of the program.
                return ''
            elif (name == 'gamedir_b2'):
                for dir in [ '/usr/games', '/opt', '/opt/games', '/usr/share/games', '/usr/local/games' ]:
                    fulldir = os.path.join(dir, 'eschalon_book_2')
                    if (os.path.isdir(os.path.join(fulldir, 'data'))):
                        return fulldir
                    if (os.path.isfile(os.path.join(fulldir, 'datapak'))):
                        return fulldir
                # If nothing found, don't just assume - return a blank string.  This way it
                # could be picked up again on future runs of the program.
                return ''
            elif (name == 'gamedir_b3'):
                for dir in [ '/usr/games', '/opt', '/opt/games', '/usr/share/games', '/usr/local/games' ]:
                    fulldir = os.path.join(dir, 'eschalon_book_3')
                    if (os.path.isfile(os.path.join(fulldir, 'datapak'))):
                        return fulldir
                # If nothing found, don't just assume - return a blank string.  This way it
                # could be picked up again on future runs of the program.
                return ''
        return self.global_default(cat, name)

    def darwin_prefsfile(self):
        """ Default prefsfile on Darwin """
        prefdir = os.path.join(os.path.expanduser('~'), 'Library', 'Preferences', app_name)
        if (not os.path.isdir(prefdir)):
            os.mkdir(prefdir)
        return os.path.join(prefdir, 'config.ini')

    def darwin_default(self, cat, name):
        """ Default values on Darwin """
        if (cat == 'paths'):
            if (name == 'savegames'):
                return os.path.join(os.path.expanduser('~'), 'Documents', 'Eschalon Book 1 Saved Games')
            elif (name == 'savegames_b2'):
                return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Basilisk Games', 'Book 2 Saved Games')
            elif (name == 'savegames_b3'):
                return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Basilisk Games', 'Book 3 Saved Games')
            elif (name == 'gamedir'):
                return '/Applications/Eschalon Book I.app'
            elif (name == 'gamedir_b2'):
                return '/Applications/Eschalon Book II.app'
            elif (name == 'gamedir_b3'):
                return '/Applications/Eschalon Book III.app'
        return self.global_default(cat, name)

    def win32_prefsfile_final(self, path):
        """ Given a path, spit out our prefsfile from that root. """
        dir = os.path.join(path, app_name)
        if (not os.path.isdir(dir)):
            os.mkdir(dir)
        return os.path.join(dir, 'config.ini')

    def win32_prefsfile(self):
        """ Default prefsfile on Windows """

        # First, use %LOCALAPPDATA% like we should be doing.
        if 'LOCALAPPDATA' in os.environ:
            appdir = os.environ['LOCALAPPDATA']
            if (os.path.isdir(appdir)):
                return self.win32_prefsfile_final(appdir)

        # ... and if not, loop through various options.  I'm having a hard
        # time coming up with a scenario where the above call would fail but
        # the ones below would work, but I feel compelled to try.
        user_dir_names = [os.path.expanduser('~')]
        if 'USERPROFILE' in os.environ:
            user_dir_names.append(os.environ['USERPROFILE'])

        # This loop will check various combinations which Shouldn't work.
        # But then again, we're already jumping into strange waters by
        # getting here in the first place, so let's be thorough.
        for user_dir_name in user_dir_names:

            # "Application Data" should be 2000, XP, 2003
            # "AppData" should be Vista, 7, 8
            for app_dir_name in ['Application Data', 'AppData']:

                # This one should work for 2000, XP, 2003
                appdir = os.path.join(user_dir_name, 'Local Settings', app_dir_name)
                if (os.path.isdir(appdir)):
                    return self.win32_prefsfile_final(appdir)

                # This one should work for Vista, 7, 8
                appdir = os.path.join(user_dir_name, app_dir_name, 'Local')
                if (os.path.isdir(appdir)):
                    return self.win32_prefsfile_final(appdir)

                # This one?  Who knows.  Seems like a good thing to try?
                appdir = os.path.join(user_dir_name, app_dir_name)
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
                return ''
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
                return ''
            elif (name == 'savegames_b3'):
                basedir = os.path.expanduser('~')
                savedir = os.path.join('Basilisk Games', 'Book 3 Saved Games')
                # Huzzah for flailing about!
                for dir in [ os.path.join(basedir, 'Local Settings', 'Application Data', savedir),
                        os.path.join(basedir, 'Application Data', savedir),
                        os.path.join(basedir, 'My Documents', savedir),
                        os.path.join(basedir, 'AppData', 'Roaming', savedir),
                        os.path.join(basedir, 'AppData', savedir)]:
                    if (os.path.isdir(dir)):
                        return dir
                return ''
            elif (name == 'gamedir'):
                for dir in [ 'C:\\Games', 'C:\\Program Files' ]:
                    testdir = os.path.join(dir, 'Eschalon Book I')
                    if (os.path.isdir(os.path.join(testdir, 'packedgraphics'))):
                        return testdir
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
                    return ''

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
                        testdir = ''

                # Close and return what we've got
                wr.Close()
                return testdir
            elif (name == 'gamedir_b2'):
                for dir in [ 'C:\\Games', 'C:\\Program Files' ]:
                    testdir = os.path.join(dir, 'Eschalon Book II')
                    if (os.path.isdir(os.path.join(testdir, 'data'))):
                        return testdir
                    if (os.path.isfile(os.path.join(testdir, 'datapak'))):
                        return testdir
                # If we got here, it wasn't found - check the registry.  If there
                # are any errors, just return our most recent testdir
                try:
                    wr = _winreg.OpenKey(
                        _winreg.HKEY_LOCAL_MACHINE,
                        'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Eschalon Book II_is1'
                        )
                except EnvironmentError, e:
                    return ''

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
                        testdir = ''

                # Close and return what we've got
                wr.Close()
                return testdir
            elif (name == 'gamedir_b3'):
                for dir in [ 'C:\\Games', 'C:\\Program Files' ]:
                    testdir = os.path.join(dir, 'Eschalon Book III')
                    if (os.path.isfile(os.path.join(testdir, 'datapak'))):
                        return testdir
                # If we got here, it wasn't found - check the registry.  If there
                # are any errors, just return our most recent testdir
                try:
                    wr = _winreg.OpenKey(
                        _winreg.HKEY_LOCAL_MACHINE,
                        'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Eschalon Book III_is1'
                        )
                except EnvironmentError, e:
                    return ''

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
                        testdir = ''

                # Close and return what we've got
                wr.Close()
                return testdir

        return self.global_default(cat, name)
