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

import os
import sys

# Load in our PyGTK deps
pygtkreq = '2.0'
try:
    import pygtk
    pygtk.require(pygtkreq)
except:
    print 'PyGTK version %s or higher is required' % pygtkreq
    sys.exit(1)

try:
    import gtk
    import gtk.glade
except:
    print 'Python GTK Modules not found'
    sys.exit(1)

import gobject

class BaseGUI:

    def prefs_init(self, prefs):

        # Prefs data object
        self.prefsobj = prefs

        # Preferences window
        self.prefsgladefile = os.path.join(os.path.dirname(__file__), 'preferences.glade')
        self.prefswTree = gtk.glade.XML(self.prefsgladefile)
        self.prefswindow = self.prefswTree.get_widget('prefswindow')
        self.gfx_req_window = self.prefswTree.get_widget('gfx_req_window')
        self.prefsview = self.prefswTree.get_widget('prefsview')
        self.prefssel = self.prefsview.get_selection()
        self.prefsnotebook = self.prefswTree.get_widget('prefsnotebook')

        # Prefs fields
        self.prefs_savegame = self.prefswTree.get_widget('savegame_chooser')
        self.prefs_gamedir = self.prefswTree.get_widget('gamedata_chooser')

        # Connect handler
        self.prefssel.connect('changed', self.on_prefs_changed)

        # Set up prefs colums
        store = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING, gobject.TYPE_INT)
        self.prefsview.set_model(store)
        col = gtk.TreeViewColumn('Icon', gtk.CellRendererPixbuf(), pixbuf = 0)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(50)
        self.prefsview.append_column(col)
        col = gtk.TreeViewColumn('Text', gtk.CellRendererText(), text = 1)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(110)
        self.prefsview.append_column(col)

        # Set up prefs rows
        pixbuf = self.prefswindow.render_icon(gtk.STOCK_OPEN, gtk.ICON_SIZE_DIALOG)
        store.set(store.append(), 0, pixbuf, 1, 'File Locations', 2, 0)
        #store.set(store.append(), 0, pixbuf, 1, 'Other', 2, 1)

    def require_gfx(self):
        while (not os.path.isfile(os.path.join(self.prefsobj.get_str('paths', 'gamedir'), 'gfx.pak'))):
            response = self.gfx_req_window.run()
            self.gfx_req_window.hide()
            if (response == gtk.RESPONSE_CANCEL):
                return False
            else:
                self.on_prefs(None)
        return True

    def on_prefs(self, widget):
        if (self.prefsobj.get_str('paths', 'savegames') != ''):
            self.prefs_savegame.set_current_folder(self.prefsobj.get_str('paths', 'savegames'))
        if (self.prefsobj.get_str('paths', 'gamedir') != ''):
            self.prefs_gamedir.set_current_folder(self.prefsobj.get_str('paths', 'gamedir'))
        response = self.prefswindow.run()
        self.prefswindow.hide()
        if (response == gtk.RESPONSE_OK):
            self.prefsobj.set_str('paths', 'savegames', self.prefs_savegame.get_filename())
            self.prefsobj.set_str('paths', 'gamedir', self.prefs_gamedir.get_filename())
            self.prefsobj.save()

    def on_prefs_changed(self, widget):
        (model, iter) = widget.get_selected()
        if (iter is not None):
            self.prefsnotebook.set_current_page(model.get(iter, 2)[0])
