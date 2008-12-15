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
import os.path

# TODO: Mac/Cygwin
# I presume that Cygwin would be identical to windows, with the exception of the
# default file paths.  Mac should be quite straightforward, using plist, though
# apparently PyGTK + Mac isn't very happy at the moment, so I'll get it... Later.

class LinuxPrefs:
    """
    Container to hold Linux preferences.  Stores everything inside a dotfile in the
    user's homedir, using ConfigParser.
    """

    def __init__(self):
        import ConfigParser
        self.filename = os.path.join(os.path.expanduser('~'), '.eschalon_b1_utils_rc')
        self.cp = ConfigParser.ConfigParser()

    def default(self, cat, name):
        if (cat == 'paths'):
            if (name == 'savegames'):
                path = os.path.join(os.path.expanduser('~'), '.eschalon_b1_saved_games')
                if (not os.path.isdir(path)):
                    path = os.path.join(os.path.expanduser('~'), 'eschalon_b1_saved_games')
                return path
            elif (name == 'gamedir'):
                return '/usr/local/games/eschalon_book_1'
        return None

    def load(self):
        if (os.path.isfile(self.filename)):
            self.cp.read(self.filename)

    def save(self):
        df = open(self.filename, 'w')
        self.cp.write(df)
        df.close()

    def set_str(self, cat, name, val):
        if (not self.cp.has_section(cat)):
            self.cp.add_section(cat)
        return self.cp.set(cat, name, val)

    def get_str(self, cat, name):
        return self.cp.get(cat, name)

class WindowsPrefs:
    """
    Container to hold Windows preferences.  Stores everything in the registry.  We
    keep a dictionary of the values internally, so that we only write out to the registry
    when something explicitly calls a save().
    """

    # TODO: None of this has been tested
    # TODO: Can I call, for instance, self.key.EnumKey(1) instead of winreg.EnumKey(self.key, 1) ?
    #       (also for QueryInfoKey, etc)
    # TODO: The EnumValue docs seem to imply I can just keep calling them?  Do I not need to get
    #       the key/value count first?  index is optional, perhaps?

    def __init__(self):
        import _winreg as winreg
        from eschalonb1 import app_name
        self.vars = {}
        self.keyname = 'Software\\Apocalyptech\\%s' % (app_name)
        try:
            self.key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.keyname)
        except EnvironmentError, e:
            self.key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.keyname)

    def default(self, cat, name):
        # TODO: I just made these paths up.
        if (cat == 'paths'):
            if (name == 'savegames'):
                return 'C:\Documents and Settings\Current User\Eschalon Something';
            elif (name == 'gamedir'):
                return 'C:\Programs and Files\Eschalon Book 1'
        return None

    def load(self):
        numkeys = winreg.QueryInfoKey(self.key)[0]
        for i in range(numkeys):
            # TODO: will this return the full key name, or just the "local" part?
            # My code here assumes just the local part
            subkey = winreg.EnumKey(self.key, i)
            subkeyobj = winreg.OpenKey(self.keyname, subkey)
            numvals = winreg.QueryInfoKey(subkeyobj)[1]
            for j in range(numvals):
                (var, val, type) = winreg.EnumValue(subkeyobj, j)
                self.set_str(subkey, var, val)
            subkeyobj.Close()

    def save(self):
        for (cat, values) in self.vars.items():
            key = winreg.CreateKey(self.key, cat)
            for (var, val) in values.items():
                # TODO: This only supports strings, I guess...
                # TODO: Do I need to specify KEY_SET_VALUE when opening the key?  Why can't I do so in Create?
                # ... and actually, I see that stuff about handle objects now; I'm doing this wrong.
                winreg.SetValue(key, var, winreg.REG_SZ, val)
            key.Close()

    def set_str(self, cat, name, val):
        if (cat not in self.vars):
            self.vars[cat] = {}
        self.vars[cat][name] = val

    def get_str(self, cat, name):
        if (cat in self.vars and name in self.vars[cat]):
            return self.vars[cat][name]
        else:
            # TODO: I wonder if I should return '' instead
            return None

class Prefs:

    def __init__(self):
        if 'win32' in sys.platform:
            self.platform = 'win32'
            self.prefs = WindowsPrefs()
        elif 'cygwin' in sys.platform:
            self.platform = 'cygwin'
            raise Exception('no cygwin support currently')
        elif 'darwin' in sys.platform:
            self.platform = 'darwin'
            raise Exception('no mac support currently')
        else:
            # Assume linux
            self.platform = 'linux'
            self.prefs = LinuxPrefs()

        # Passthrough functions
        self.default = self.prefs.default
        self.get_str = self.prefs.get_str
        self.set_str = self.prefs.set_str
        self.save = self.prefs.save
        self.load = self.prefs.load

        # Initialize our defaults and load, if we can
        self.set_defaults()
        self.load()

    def set_defaults(self):
        for vars in [('paths', 'savegames'), ('paths', 'gamedir')]:
            self.set_str(vars[0], vars[1], self.default(vars[0], vars[1]))
