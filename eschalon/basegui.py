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

import os
import sys
from struct import unpack

try:
    import gtk
    import gobject
    import pango
except:
    print 'Python GTK Modules not found: %s' % (str(e))
    print 'Hit enter to exit...'
    sys.stdin.readline()
    sys.exit(1)

from eschalon import constants as c
from eschalon.scripteditor import ScriptEditor

class WrapLabel(gtk.Label):

    # Taken from http://git.gnome.org/browse/meld/tree/meld/ui/wraplabel.py
    # Re-used here because, as it turns out, regular gtk.Label objects will
    # *not* resize automatically when the parent changes, which in some
    # circumstances looks really ugly.  This will fix it right up.

    # Copyright (c) 2005 VMware, Inc.
    #
    # Permission is hereby granted, free of charge, to any person obtaining a copy
    # of this software and associated documentation files (the "Software"), to deal
    # in the Software without restriction, including without limitation the rights
    # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    # copies of the Software, and to permit persons to whom the Software is
    # furnished to do so, subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be included in
    # all copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    # SOFTWARE.

    # Python translation from wrapLabel.{cc|h} by Gian Mario Tagliaretti
    __gtype_name__ = 'WrapLabel'

    def __init__(self, str=None):
        gtk.Label.__init__(self)

        self.__wrap_width = 0
        self.layout = self.get_layout()
        self.layout.set_wrap(pango.WRAP_WORD)

        if str != None:
            self.set_markup(str)

        self.set_alignment(0.0, 0.0)

    def do_size_request(self, requisition):
        layout = self.get_layout()
        width, height = layout.get_pixel_size()
        requisition.width = 0
        requisition.height = height

    def do_size_allocate(self, allocation):
        gtk.Label.do_size_allocate(self, allocation)
        self.__set_wrap_width(allocation.width)

    def set_text(self, str):
        gtk.Label.set_text(self, str)
        self.__set_wrap_width(self.__wrap_width)

    def set_markup(self, str):
        gtk.Label.set_markup(self, str)
        self.__set_wrap_width(self.__wrap_width)

    def __set_wrap_width(self, width):
        if width == 0:
            return
        layout = self.get_layout()
        layout.set_width(width * pango.SCALE)
        if self.__wrap_width != width:
            self.__wrap_width = width
            self.queue_resize()

class BaseGUI(object):

    # Constants
    ITEM_NONE=0
    ITEM_EQUIP=1
    ITEM_INV=2
    ITEM_READY=3
    ITEM_MAP=4

    def base_init(self):
        """
        Performs any options we'll need for a GUI
        """

        # This may be kind of silly actually, but it's rather entrenched now.
        # Anyway, we're caching GUI elements here, by name.
        self.widgetcache = {}

        # This is actually only used on the character editor, but whatever.
        # Stores the vanilla labels which "should" be in place for an unmodified
        # variable.
        self.labelcache = {}

        # Find out if we have NumPy installed.  There's a bug in pygtk (or,
        # at least, a bug SOMEWHERE) where if numpy isn't installed, a call
        # to gtk.gdk.Pixbuf.get_pixels_array() will segfault Python, which
        # isn't catchable.  So instead of letting that happen, we'll just find
        # out here.  The bug: https://bugzilla.gnome.org/show_bug.cgi?id=626683
        try:
            import numpy
            self.have_numpy = True
        except ImportError, e:
            self.have_numpy = False

    def datafile(self, file):
        return os.path.join(self.datadir, file)

    def path_init(self):
        # Figure out if we're running inside library.zip (which would mean that we've
        # been packaged on Windows, and need to modify where we look for data files
        # slightly.)  It would probably make more sense to check some other environment
        # var here, really, but we'll just do this for now.
        if (os.path.dirname(__file__).find('library.zip') == -1):
            self.datadir = os.path.join(os.path.dirname(__file__), '..', 'data')
        else:
            self.datadir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

    def prefs_init(self, prefs):

        # Prefs data object
        self.prefsobj = prefs

        # Preferences window
        self.prefsbuilder = gtk.Builder()
        self.prefsbuilder.add_from_file(self.datafile('preferences.ui'))
        self.prefswindow = self.prefsbuilder.get_object('prefswindow')
        self.gfx_req_window = self.prefsbuilder.get_object('gfx_req_window')
        self.gfx_opt_window = self.prefsbuilder.get_object('gfx_opt_window')
        self.prefsview = self.prefsbuilder.get_object('prefsview')
        self.prefssel = self.prefsview.get_selection()
        self.prefsnotebook = self.prefsbuilder.get_object('prefsnotebook')

        # Prefs fields
        self.prefs_savegame = self.prefsbuilder.get_object('savegame_chooser')
        self.prefs_savegame_b2 = self.prefsbuilder.get_object('savegame_b2_chooser')
        self.prefs_gamedir = self.prefsbuilder.get_object('gamedata_chooser')
        self.prefs_gamedir_b2 = self.prefsbuilder.get_object('gamedata_b2_chooser')
        self.prefs_default_zoom = self.prefsbuilder.get_object('prefs_default_zoom')
        self.prefs_warn_global = self.prefsbuilder.get_object('prefs_warn_global')
        self.prefs_warn_slowzip = self.prefsbuilder.get_object('prefs_warn_slowzip')

        # Explicitly set our widget names (needed for gtk+ 2.20 compatibility)
        # See https://bugzilla.gnome.org/show_bug.cgi?id=591085
        for object in self.prefsbuilder.get_objects():
            try:
                builder_name = gtk.Buildable.get_name(object)
                if builder_name:
                    object.set_name(builder_name)
            except TypeError:
                pass

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
        pixbuf = self.prefswindow.render_icon(gtk.STOCK_CLEAR, gtk.ICON_SIZE_DIALOG)
        store.set(store.append(), 0, pixbuf, 1, 'Map Editor', 2, 1)

        # Update the text on our graphics popups
        if c.book == 1:
            gfxfile = 'gfx.pak'
        else:
            gfxfile = 'datapak'
        opt_label = self.prefsbuilder.get_object('gfx_opt_window_mainlabel')
        opt_label.set_markup('We couldn\'t locate the file "%s," which can be used by '
            'this program to enhance the GUI.  It\'s not required, but it does look '
            'nicer.'
            "\n\n"
            '%s can be found in the Eschalon Book %d installation folder.  Hit OK to '
            'bring up the preferences screen, where you can browse to the installation '
            'folder and continue.  Alternately, hit Cancel to continue.' % (gfxfile, gfxfile, c.book))
        req_label = self.prefsbuilder.get_object('gfx_req_window_mainlabel')
        req_label.set_markup('We couldn\'t locate the file "%s," which this program needs '
                'to operate.'
                "\n\n"
                '%s can be found in the Eschalon Book %d installation folder.  Hit OK to '
                'bring up the preferences screen, where you can browse to the installation '
                'folder and continue.  Alternately, hit Cancel to exit this program.' % (
                    gfxfile, gfxfile, c.book))

    def item_signals(self):
        """ Returns the signals that need to be attached for items. """
        return {
                'on_singleval_changed_str': self.on_singleval_changed_str,
                'on_singleval_changed_int': self.on_singleval_changed_int,
                'on_singleval_changed_int_itempic': self.on_singleval_changed_int_itempic,
                'on_singleval_changed_float': self.on_singleval_changed_float,
                'on_dropdown_changed': self.on_dropdown_changed,
                'on_type_dropdown_changed': self.on_type_dropdown_changed,
                'on_checkbox_changed': self.on_checkbox_changed,
                'on_checkbox_bit_changed': self.on_checkbox_bit_changed,
                'on_modifier_changed': self.on_modifier_changed,
                'on_b2_modifier_changed': self.on_b2_modifier_changed,
                'on_item_close_clicked': self.on_item_close_clicked,
                'open_itemsel': self.open_itemsel,
                'imgsel_on_motion': self.imgsel_on_motion,
                'imgsel_on_expose': self.imgsel_on_expose,
                'imgsel_on_clicked': self.imgsel_on_clicked,
                'on_bgcolor_img_clicked': self.on_bgcolor_img_clicked,
                'bypass_delete': self.bypass_delete,
                'on_b2_item_attr3_treeview_clicked': self.on_b2_item_attr3_treeview_clicked,
                }

    def register_widget(self, name, widget, doname=True):
        if doname:
            widget.set_name(name)
        #if name in self.widgetcache:
        #    print 'WARNING: Created duplicate widget "%s"' % (name)
        self.widgetcache[name] = widget

    def get_widget(self, name):
        """ Returns a widget from our cache, or from builder obj if it's not present in the cache. """
        try:
            return self.widgetcache[name]
        except KeyError:
            self.register_widget(name, self.builder.get_object(name), False)
            return self.widgetcache[name]

    def get_label_cache(self, name):
        """ Returns a widget and the proper label for the widget (to save on processing) """
        labelname = '%s_label' % (name)
        try:
            return (self.get_widget(labelname), self.labelcache[labelname])
        except KeyError:
            widget = self.get_widget(labelname)
            self.labelcache[labelname] = widget.get_label()
            return (widget, self.labelcache[labelname])

    @staticmethod
    def userdialog(type, buttons, title, markup, parent=None):
        """
        Shows a dialog for the user, with the given attributes.
        """
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                type, buttons)
        if parent:
            dialog.set_transient_for(parent)
            dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.set_title(title)
        dialog.set_property('skip-taskbar-hint', False)
        dialog.set_markup(markup)
        result = dialog.run()
        dialog.destroy()
        return result

    @staticmethod
    def infodialog(title, markup, parent=None):
        return BaseGUI.userdialog(gtk.MESSAGE_INFO, gtk.BUTTONS_OK, title, markup, parent)

    @staticmethod
    def warningdialog(title, markup, parent=None):
        return BaseGUI.userdialog(gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, title, markup, parent)

    @staticmethod
    def errordialog(title, markup, parent=None):
        return BaseGUI.userdialog(gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, title, markup, parent)

    @staticmethod
    def confirmdialog(title, markup, parent=None):
        return BaseGUI.userdialog(gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, title, markup, parent)

    def set_book_elem_visibility(self, classname, show):
        """
        Show or hide form elements based on the book version
        """
        if show:
            for elem in classname.form_elements:
                widget = self.get_widget(elem)
                if widget:
                    widget.show()
        else:
            for elem in classname.form_elements:
                widget = self.get_widget(elem)
                if widget:
                    widget.hide()

    def item_gui_finish(self, book):
        """
        Called when we load a new character, this will update the item form with
        elements which are dynamic based on the Book
        """

        ###
        ### Item Type and Subtype dropdowns
        ###
        type_dd = self.get_widget('type')
        type_dd.get_model().clear()
        for type in c.typetable.values():
            type_dd.append_text(type)
        subtype_dd = self.get_widget('subtype')
        subtype_dd.get_model().clear()
        subtype_dd.append_text('(none)')
        for subtype in c.skilltable.values():
            subtype_dd.append_text(subtype)

        ###
        ### Item attribute modifier dropdowns
        ### Note that technically we don't need to do this dynamically, since
        ### these dropdowns only exist for Book 2.
        ###
        if book == 2:
            boxes = []
            for i in range(1, 4):
                boxes.append(self.get_widget('attr_modified_%d' % (i)))
            attributes = c.itemeffecttable.values()
            for box in boxes:
                box.get_model().clear()
                box.append_text('')
                for attribute in attributes:
                    box.append_text(attribute)

            # Also, add in a couple of WrapLabels...
            align = self.get_widget('b2_modifier_3_infoalign')
            label = WrapLabel('The third modifier is the only one which can '
                    'have a negative value, and uses four bytes instead of '
                    'one.  Potions and reagents use a flag system (R+R=P).  '
                    'Double-click to set one of those values, if you want.')
            label.show()
            align.add(label)

            align = self.get_widget('b2_item_picid_notealign')
            label = WrapLabel('<i>Note: Picture IDs in Book 2 are only '
                    'unique within their groups: armor, weapons, '
                    'magic/alchemy, or "other."</i>')
            label.show()
            align.add(label)

        ###
        ### Fix some tooltips
        ###
        if book == 1:
            self.get_widget('visibility').set_tooltip_text('This is generally 1 for ordinary items, and 3 for items which the character hasn\'t identified yet.  Other values\' meanings are unknown.');
            self.get_widget('quantity').set_tooltip_text('This value only makes sense when \'Can Stack\' is checked, above.  Ordinarily zero for items which can\'t be stacked.');
        else:
            self.get_widget('visibility').set_tooltip_text('This is 1 for items you\'ve identified - other numbers represent the difficulty of identifying the item.  Bar of Mithril is set to 9, for reference.')
            self.get_widget('quantity').set_tooltip_text('This is usually 1 even if \'Can Stack\' is set to No.')

        ###
        ### Glade is seriously problematic; handle this TreeView connecting
        ### stuff by hand.
        ###
        col = gtk.TreeViewColumn('Potion', gtk.CellRendererText(), text = 0)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(150)
        col.set_clickable(True)
        col.set_sort_column_id(0)
        self.get_widget('b2_potion_magic_treeview').append_column(col)
        col = gtk.TreeViewColumn('Value', gtk.CellRendererText(), text = 1)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(150)
        col.set_clickable(True)
        col.set_sort_column_id(1)
        self.get_widget('b2_potion_magic_treeview').append_column(col)

        col = gtk.TreeViewColumn('Reagent', gtk.CellRendererText(), text = 0)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(150)
        col.set_clickable(True)
        col.set_sort_column_id(0)
        self.get_widget('b2_reagent_magic_treeview').append_column(col)
        col = gtk.TreeViewColumn('Value', gtk.CellRendererText(), text = 1)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        col.set_fixed_width(150)
        col.set_clickable(True)
        col.set_sort_column_id(1)
        self.get_widget('b2_reagent_magic_treeview').append_column(col)

        ###
        ### Script Editor Window
        ###
        self.script_editor = ScriptEditor(self.window)
        self.setup_script_editor_launcher(self.get_widget('script_hbox'), self.get_widget('script'))

    def launch_script_editor(self, widget, script_entry):
        """
        Launches our script editor
        """
        res = self.script_editor.launch(script_entry.get_text())
        if res == gtk.RESPONSE_OK:
            script_entry.set_text(self.script_editor.get_command_aggregate())

    def setup_script_editor_launcher(self, container, widget):
        """
        Adds a button to launch the script editor, given the container to put
        it in, and a widget whose .get_text() will provide the script text.
        """
        align = gtk.Alignment(0, .5, 1, 1)
        align.set_padding(0, 0, 6, 0)
        button = gtk.Button()
        button.add(gtk.image_new_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_BUTTON))
        button.set_tooltip_text('Launch Script Editor')
        button.connect('clicked', self.launch_script_editor, (widget))
        align.add(button)
        container.pack_start(align, False)
        align.show_all()

    def bypass_delete(self, widget, event):
        """
        Used to prevent a delete-event from actually deleting our object
        (typically a Window, in our case).  Instead, just hide the object.
        """
        widget.hide()
        return True

    def gamedir_set_b1(self):
        return (os.path.isfile(os.path.join(self.prefsobj.get_str('paths', 'gamedir'), 'gfx.pak')))

    def gamedir_set_b2(self):
        return (os.path.isfile(os.path.join(self.prefsobj.get_str('paths', 'gamedir_b2'), 'datapak')))

    def gamedir_set(self, book=None):
        if book is None:
            if c.book == 1:
                return self.gamedir_set_b1()
            else:
                return self.gamedir_set_b2()
        else:
            if book == 1:
                return self.gamedir_set_b1()
            else:
                return self.gamedir_set_b2()

    def get_savegame_dir_key(self):
        if c.book == 1:
            return 'savegames'
        else:
            return 'savegames_b2'

    def get_gamedir_key(self):
        if c.book == 1:
            return 'gamedir'
        else:
            return 'gamedir_b2'

    def get_current_savegame_dir(self):
        """
        Returns the appropriate savegame dir, depending on if we're book 1 or 2
        """
        return self.prefsobj.get_str('paths', self.get_savegame_dir_key())

    def get_current_gamedir(self):
        """
        Returns the appropriate gamedir, depending on if we're book 1 or 2
        """
        return self.prefsobj.get_str('paths', self.get_gamedir_key())

    def optional_gfx(self):
        if (not self.gamedir_set()):
            response = self.gfx_opt_window.run()
            self.gfx_opt_window.hide()
            if (response == gtk.RESPONSE_OK):
                self.on_prefs(None)

    def require_gfx(self):
        while (not self.gamedir_set()):
            response = self.gfx_req_window.run()
            self.gfx_req_window.hide()
            if (response == gtk.RESPONSE_CANCEL):
                return False
            else:
                self.on_prefs(None)
        return True

    def on_prefs(self, widget):
        changed = False
        if (self.gamedir_set()):
            alert_changed = True
        else:
            alert_changed = False
        if (self.prefsobj.get_int('mapgui', 'default_zoom')):
            self.prefs_default_zoom.set_value(self.prefsobj.get_int('mapgui', 'default_zoom'))
        cur_gamedir = self.get_current_gamedir()
        cur_savegamedir = self.get_current_savegame_dir()
        if c.book == 1:
            self.prefsbuilder.get_object('b1_dir_tab').show()
            self.prefsbuilder.get_object('b2_dir_tab').hide()
            gui_gamedir = self.prefs_gamedir
            gui_savegamedir = self.prefs_savegame
            look_for = 'gfx.pak'
        else:
            self.prefsbuilder.get_object('b1_dir_tab').hide()
            self.prefsbuilder.get_object('b2_dir_tab').show()
            gui_gamedir = self.prefs_gamedir_b2
            gui_savegamedir = self.prefs_savegame_b2
            look_for = 'datapak'

        # In case we have a blank value stored in the prefs file, re-attempt to set it
        # from the default (should theoretically return '' anyway if we can't)
        if cur_gamedir == '':
            cur_gamedir = self.prefsobj.default('paths', self.get_gamedir_key())
        if cur_savegamedir == '':
            cur_savegamedir = self.prefsobj.default('paths', self.get_savegame_dir_key())

        if cur_gamedir != '':
            gui_gamedir.set_current_folder(cur_gamedir)
        if cur_savegamedir != '':
            gui_savegamedir.set_current_folder(cur_savegamedir)
        self.prefs_warn_global.set_active(self.prefsobj.get_bool('mapgui', 'warn_global_map'))
        self.prefs_warn_slowzip.set_active(self.prefsobj.get_bool('mapgui', 'warn_slow_zip'))
        #self.prefsnotebook.set_current_page(0)
        self.prefswindow.set_transient_for(self.window)
        response = self.prefswindow.run()
        self.prefswindow.hide()
        if (response == gtk.RESPONSE_OK):
            self.prefsobj.set_int('mapgui', 'default_zoom', int(self.prefs_default_zoom.get_value()))
            self.prefsobj.set_bool('mapgui', 'warn_global_map', self.prefs_warn_global.get_active())
            self.prefsobj.set_bool('mapgui', 'warn_slow_zip', self.prefs_warn_slowzip.get_active())

            # Save our new game directory.  We actually only want to save under two conditions:
            #   1) We had a previous game directory set already
            # -or-
            #   2) We can actually find the gfx.pak or datapak (as the case may be)
            #
            # We check for these because our FileChooserDialogs will *always* return a filename for
            # us, but will just be the current directory if there wasn't anything in there previously.
            # So if our old value was blank, we'll assume that the dialog was just defaulting to
            # the current dir, if the graphics pack wasn't found.
            new_gamedir = gui_gamedir.get_filename()
            if (cur_gamedir != '' or os.path.exists(os.path.join(new_gamedir, look_for))):
                self.prefsobj.set_str('paths', self.get_gamedir_key(), new_gamedir)
                if cur_gamedir != new_gamedir:
                    changed = True

            # Similar logic applies to the savegame directory
            new_savegamedir = gui_savegamedir.get_filename()
            if (cur_savegamedir != '' or os.path.exists(os.path.join(new_savegamedir, 'slot1'))):
                self.prefsobj.set_str('paths', self.get_savegame_dir_key(), new_savegamedir)

            self.prefsobj.save()
        return (changed, alert_changed)

    def on_prefs_changed(self, widget):
        (model, iter) = widget.get_selected()
        if (iter is not None):
            self.prefsnotebook.set_current_page(model.get(iter, 2)[0])

    def useful_combobox(self, box):
        ls = gtk.ListStore(gobject.TYPE_STRING)
        box.set_model(ls)
        cell = gtk.CellRendererText()
        box.pack_start(cell, True)
        box.add_attribute(cell, 'text', 0)

    def useful_comboboxentry(self, box):
        box.set_model(gtk.ListStore(gobject.TYPE_STRING))
        box.set_text_column(0)

    def get_comp_objects(self):
        """ Get the objects to compare against while checking for form changes. """
        if (self.curitemtype == self.ITEM_EQUIP):
            obj = self.char.__dict__[self.curitem]
            origobj = self.origchar.__dict__[self.curitem]
        elif (self.curitemtype == self.ITEM_INV):
            obj = self.char.inventory[self.curitem[0]][self.curitem[1]]
            origobj = self.origchar.inventory[self.curitem[0]][self.curitem[1]]
        elif (self.curitemtype == self.ITEM_READY):
            obj = self.char.readyitems[self.curitem]
            origobj = self.origchar.readyitems[self.curitem]
        elif (self.curitemtype == self.ITEM_MAP):
            obj = self.map.squares[self.sq_y][self.sq_x].scripts[self.curitem[1]].items[self.curitem[0]]
            origobj = obj
        else:
            obj = self.char
            origobj = self.origchar
        return (obj, origobj)

    def on_singleval_changed_str(self, widget):
        """ What to do when a string value changes. """
        wname = widget.get_name()
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_text()
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_singleval_changed_int(self, widget):
        """ What to do when an int value changes. """
        wname = widget.get_name()
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = int(widget.get_value())
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_singleval_changed_float(self, widget):
        """ What to do when an int value changes. """
        wname = widget.get_name()
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_value()
        # Note that for floats, we shouldn't do exact precision, hence the 1e-6 comparison here.
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((abs(origobj.__dict__[wname] - obj.__dict__[wname])<1e-6), wname, labelwidget, label)

    def update_itempic_image(self):
        if (self.gfx is not None):
            (obj, origobj) = self.get_comp_objects()
            self.get_widget('item_pic_image').set_from_pixbuf(self.gfx.get_item(obj))

    def on_singleval_changed_int_itempic(self, widget):
        """ Special-case to handle changing the item picture properly. """
        self.on_singleval_changed_int(widget)
        self.update_itempic_image()
    
    def on_dropdown_changed(self, widget):
        """ What to do when a dropdown is changed """
        wname = widget.get_name()
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_active()
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)
    
    def on_type_dropdown_changed(self, widget):
        """
        What to do when the item type dropdown is changed.
        Only has an actual effect in Book 2, though technically Book 1 will go through
        the motions as well.
        """
        self.on_dropdown_changed(widget)
        self.update_itempic_image()

    def on_checkbox_changed(self, widget):
        """ What to do when a regular checkbox changes. """
        wname = widget.get_name()
        ischecked = widget.get_active()
        (obj, origobj) = self.get_comp_objects()
        if (ischecked):
            obj.__dict__[wname] = 1
        else:
            obj.__dict__[wname] = 0
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_checkbox_bit_changed(self, widget):
        """ What to do when a checkbox changes, and it's a bitfield. """
        wname = widget.get_name()
        ischecked = widget.get_active()
        (shortname, mask) = wname.rsplit('_', 1)
        mask = int(mask, 16)
        (obj, origobj) = self.get_comp_objects()
        if (ischecked):
            obj.__dict__[shortname] = obj.__dict__[shortname] | mask
        else:
            obj.__dict__[shortname] = obj.__dict__[shortname] & ~mask
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[shortname] & mask == obj.__dict__[shortname] & mask), wname, labelwidget, label)

    def on_modifier_changed(self, widget):
        """ What to do when our attr or skill modifier changes. """
        wname = widget.get_name()
        (which, type) = wname.rsplit('_', 1)
        modifiertext = '%s_modifier' % (which)
        modifiedtext = '%s_modified' % (which)
        modifier = int(self.get_widget(modifiertext).get_value())
        modified = self.get_widget(modifiedtext).get_active()
        (obj, origobj) = self.get_comp_objects()
        if (wname == modifiertext):
            obj.__dict__[modifiertext] = modifier
        elif (wname == modifiedtext):
            obj.__dict__[modifiedtext] = modified
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(which)
            self.set_changed_widget((origobj.__dict__[modifiertext] == obj.__dict__[modifiertext] and
                origobj.__dict__[modifiedtext] == obj.__dict__[modifiedtext]), which, labelwidget, label)

    def on_b2_modifier_changed(self, widget):
        """ What to do when a book 2 item attribute changes. """
        if c.book != 2:
            return
        wname = widget.get_name()
        num = int(wname.split('_')[-1])
        modifiertext = 'attr_modifier_%d' % (num)
        modifiedtext = 'attr_modified_%d' % (num)
        modifier = int(self.get_widget(modifiertext).get_value())
        modified = self.get_widget(modifiedtext).get_active()
        (obj, origobj) = self.get_comp_objects()
        if (wname == modifiertext):
            obj.__dict__[modifiertext] = modifier
        elif (wname == modifiedtext):
            obj.__dict__[modifiedtext] = modified
        if num == 3:
            if obj.attr_modifier_3 < 0:
                self.get_widget('attr_modified_plusminus_3').set_text('')
            else:
                self.get_widget('attr_modified_plusminus_3').set_text('+')
        if (self.curitemtype != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(modifiertext)
            self.set_changed_widget((origobj.__dict__[modifiertext] == obj.__dict__[modifiertext] and
                origobj.__dict__[modifiedtext] == obj.__dict__[modifiedtext]), modifiertext, labelwidget, label)

    def on_item_close_clicked(self, widget=None, event=None, dohide=True):
        if (self.curitemtype == self.ITEM_EQUIP):
            self.populate_equip_button(self.curitem)
        elif (self.curitemtype == self.ITEM_INV):
            self.populate_inv_button(self.curitem[0], self.curitem[1])
        elif (self.curitemtype == self.ITEM_READY):
            self.populate_ready_button(self.curitem)
        elif (self.curitemtype == self.ITEM_MAP):
            self.populate_mapitem_button(self.curitem[0], self.curitem[1])
        if (self.curitemtype != self.ITEM_MAP):
            for name in self.itemchanged.keys():
                (labelwidget, label) = self.get_label_cache(name)
                self.set_changed_widget(True, name, labelwidget, label, False)
            self.itemchanged = {}
            self.curitemtype = self.ITEM_NONE
        if (dohide):
            self.itemwindow.hide()
        return True

    def populate_item_button(self, item, widget, imgwidget, tablewidget):
        str = ''
        if (item.item_name == ''):
            str = '<i>(None)</i>'
        elif (item.type == 0):
            str = '<i>%s (no Type specified)</i>' % (item.item_name)
        else:
            if (item.canstack and item.quantity>1):
                str = '<i>(%d)</i> ' % (item.quantity)
            if (len(item.item_name) > 0):
                str = str + item.item_name
            else:
                str = str + '<i>(No name)</i>'
            if (item.hasborder()):
                str = '<span color="blue">' + str + '</span>'
        widget.set_markup(str)
        if (item.item_name == '' or self.gfx is None):
            imgwidget.set_from_stock(gtk.STOCK_EDIT, 4)
        else:
            imgwidget.set_from_pixbuf(self.gfx.get_item(item, 26))
        # to resize buttons, we have to do this:
        tablewidget.check_resize()
        # ... that may be a gtk+ bug, have to submit that to find out.
        # http://bugzilla.gnome.org/show_bug.cgi?id=548094

    def populate_itemform_from_item(self, item):
        """ Populates the Item GUI from the given object. """

        self.get_widget('item_name').set_text(item.item_name)
        self.get_widget('type').set_active(item.type)
        self.get_widget('subtype').set_active(item.subtype)
        self.get_widget('pictureid').set_value(item.pictureid)
        self.get_widget('value').set_value(item.value)
        self.get_widget('weight').set_value(item.weight)
        self.get_widget('basedamage').set_value(item.basedamage)
        self.get_widget('basearmor').set_value(item.basearmor)

        if item.book == 1:
            for key in c.flagstable.keys():
                if (item.flags & key == key):
                    self.get_widget('flags_%04X' % (key)).set_active(True)
                else:
                    self.get_widget('flags_%04X' % (key)).set_active(False)

            self.get_widget('attr_modifier').set_value(item.attr_modifier)
            self.get_widget('attr_modified').set_active(item.attr_modified)
            self.get_widget('skill_modifier').set_value(item.skill_modifier)
            self.get_widget('skill_modified').set_active(item.skill_modified)
            self.get_widget('incr').set_active(item.incr)

            self.get_widget('hitpoint').set_value(item.hitpoint)
            self.get_widget('mana').set_value(item.mana)
            self.get_widget('tohit').set_value(item.tohit)
            self.get_widget('damage').set_value(item.damage)
            self.get_widget('armor').set_value(item.armor)
        else:
            self.get_widget('cur_hp').set_value(item.cur_hp)
            self.get_widget('max_hp').set_value(item.max_hp)
            self.get_widget('attr_modifier_1').set_value(item.attr_modifier_1)
            self.get_widget('attr_modified_1').set_active(item.attr_modified_1)
            self.get_widget('attr_modifier_2').set_value(item.attr_modifier_2)
            self.get_widget('attr_modified_2').set_active(item.attr_modified_2)
            self.get_widget('attr_modifier_3').set_value(item.attr_modifier_3)
            self.get_widget('attr_modified_3').set_active(item.attr_modified_3)
            self.get_widget('unknownflag').set_value(item.unknownflag)
            self.get_widget('itemunknownc1').set_value(item.itemunknownc1)

        self.get_widget('visibility').set_value(item.visibility)
        if item.book == 1:
            self.get_widget('duration').set_value(item.duration)
        if (item.canstack):
            self.get_widget('canstack').set_active(True)
        else:
            self.get_widget('canstack').set_active(False)
        self.get_widget('quantity').set_value(item.quantity)
        self.get_widget('script').set_text(item.script)
        self.get_widget('zero1').set_value(item.zero1)
        self.get_widget('emptystr').set_text(item.emptystr)

        # Now let's manually throw our 'changed' procedures
        # This will almost always result in duplicate calls because of the
        # set_text() and set_value() calls, but we need to do it so that
        # values left over from previous items don't interfere with our
        # 'changed' labels.  As a side note, because of the __dict__ construct,
        # there's really no reason not to just use these same arrays for doing
        # the actual set_text() and set_value() calls, as well.
        #
        # One more note: we've left off the attr_modified and skill_modified
        # controls from here, because of the compound check function
        if item.book == 1:
            strvals = [ 'item_name', 'script', 'emptystr' ]
            dropdownvals = [ 'type', 'subtype', 'incr' ]
            intvals = [ 'value', 'basedamage', 'basearmor',
                    'hitpoint', 'mana', 'tohit', 'damage', 'armor',
                    'visibility', 'duration', 'quantity', 'zero1' ]
            floatvals = [ 'weight' ]
            checkboxvals = [ 'canstack' ]
            checkboxbitvals = [ 'flags_0003' ]
            modifiervals = [ 'attr_modifier', 'skill_modifier' ]
            b2modifiervals = [ ]
        else:
            strvals = [ 'item_name', 'script', 'emptystr' ]
            dropdownvals = [ 'type', 'subtype' ]
            intvals = [ 'value', 'basedamage', 'basearmor',
                    'visibility', 'quantity', 'zero1',
                    'cur_hp', 'max_hp',
                    'unknownflag', 'itemunknownc1' ]
            floatvals = [ 'weight' ]
            checkboxvals = [ 'canstack' ]
            checkboxbitvals = [ ]
            modifiervals = [ ]
            b2modifiervals = [ 'attr_modifier_1', 'attr_modifier_2', 'attr_modifier_3' ]
        for val in strvals:
            self.on_singleval_changed_str(self.get_widget(val))
        for val in dropdownvals:
            self.on_dropdown_changed(self.get_widget(val))
        for val in intvals:
            self.on_singleval_changed_int(self.get_widget(val))
        for val in floatvals:
            self.on_singleval_changed_float(self.get_widget(val))
        for val in checkboxvals:
            self.on_checkbox_changed(self.get_widget(val))
        for val in checkboxbitvals:
            self.on_checkbox_bit_changed(self.get_widget(val))
        for val in modifiervals:
            self.on_modifier_changed(self.get_widget(val))
        for val in b2modifiervals:
            self.on_b2_modifier_changed(self.get_widget(val))
        self.on_singleval_changed_int_itempic(self.get_widget('pictureid'))

    def gui_item_label(self, label, name):
        """ Generate a Label for an inventory item. """
        itemlabel = gtk.Label(label)
        itemlabel.set_alignment(1, 0.5)
        self.register_widget(name, itemlabel)
        itemlabel.show()
        return itemlabel

    def gui_item(self, name, itemcallback, itemactioncallback):
        """ Generates the whole block for an item button, including cut/paste/etc... """
        hbox = gtk.HBox()
        hbox.show()
        self.register_widget('%s_container' % (name), hbox)

        align = gtk.Alignment(0, 0.5, 0, 1)
        align.set_size_request(-1, 35)
        align.show()
        hbox.pack_start(align, False)

        itembutton = gtk.Button()
        itembutton.show()
        self.register_widget('%s_button' % name, itembutton)
        itembutton.connect('clicked', itemcallback)
        align.add(itembutton)
        
        itembutton_hbox = gtk.HBox()
        itembutton_hbox.show()
        itembutton.add(itembutton_hbox)

        buttonimg = gtk.Image()
        buttonimg.show()
        self.register_widget('%s_image' % name, buttonimg)
        itembutton_hbox.pack_start(buttonimg, False)

        buttonlabel = gtk.Label('')
        buttonlabel.show()
        buttonlabel.set_padding(7, 0)
        self.register_widget('%s_text' % name, buttonlabel)
        itembutton_hbox.pack_start(buttonlabel, True)

        expander = gtk.Expander()
        expander.show()
        hbox.pack_start(expander, True, True)

        exphbox = gtk.HBox()
        exphbox.show()
        expander.add(exphbox)

        divlabel = gtk.Label('')
        divlabel.show()
        divlabel.set_size_request(20, -1)
        exphbox.pack_start(divlabel, False)

        exphbox.pack_start(self.gui_itemedit_button(name, 'Cut', 'cut', gtk.STOCK_CUT, itemactioncallback), False)
        exphbox.pack_start(self.gui_itemedit_button(name, 'Copy', 'copy', gtk.STOCK_COPY, itemactioncallback), False)
        exphbox.pack_start(self.gui_itemedit_button(name, 'Paste', 'paste', gtk.STOCK_PASTE, itemactioncallback), False)
        exphbox.pack_start(self.gui_itemedit_button(name, 'Delete', 'delete', gtk.STOCK_DELETE, itemactioncallback), False)

        return hbox

    def gui_itemedit_button(self, itemname, name, action, stockimage, callback):
        """ Generates a single 'action' button for an item (cut/paste/etc) """
        button = gtk.Button()
        button.show()
        self.register_widget('%s_%s' % (itemname, action), button)
        button.connect('clicked', callback)
        button.set_tooltip_text(name)

        image = gtk.Image()
        image.show()
        image.set_from_stock(stockimage, 1)
        button.add(image)

        return button

    def open_itemsel(self, widget):
        if (self.gfx is not None):
            self.imgsel_launch(self.get_widget('pictureid'),
                    self.gfx.item_dim, self.gfx.item_dim, self.gfx.item_cols, self.gfx.item_rows,
                    self.gfx.get_item,
                    False, 0,
                    self.imgsel_item_creation_func)

    def imgsel_item_creation_func(self, id):
        """
        Creates a fake Item object with the given picid.
        """
        (obj, origobj) = self.get_comp_objects()
        item = obj.replicate()
        item.pictureid = id
        return item

    def imgsel_init_bgcolor(self):
        (x, y) = self.imgsel_bgcolor_img.get_size_request()
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, x, y)
        steps = 4
        max = 255
        stepval = int(max/steps)
        stepvals = []
        for i in range(steps):
            stepvals.insert(0, max-(stepval*i))
        stepvals.insert(0, 0)
        stepwidth = int(x/(steps+1))
        temppixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, stepwidth, y)
        for (i, val) in enumerate(stepvals):
            color = (val<<24) + (val<<16) + (val<<8) + 255
            temppixbuf.fill(color)
            temppixbuf.copy_area(0, 0, stepwidth, y, pixbuf, (i*stepwidth), 0)
        # We have to connect this in the code because there's no interface to do so in Glade
        self.imgsel_bgcolor_event.connect('button-press-event', self.on_bgcolor_img_clicked)
        self.imgsel_bgcolor_img.set_from_pixbuf(pixbuf)
        self.imgsel_bgcolor_pixbuf = pixbuf

    def imgsel_launch(self, widget, width, height, cols, rows, getfunc, bgcolor_select=True, offset=0, getfunc_obj_func=None):
        """
        Launches a window to select graphics from one of our files.
        widget - the spinbutton widget we'll be populating once chosen
        width/height/cols/rows - dimensions of the graphics file to use
        getfunc - function (in Gfx) to call to get the individual graphics
        bgcolor_select - whether to show the background color select area
        offset - not sure, actually
        getfunc_req_obj - Does our getfunc require an object, rather than the ID?
        """
        self.imgsel_init = False
        self.imgsel_clean = []
        self.imgsel_window = self.get_widget('imgselwindow')
        if (self.curitemtype == self.ITEM_MAP):
            self.imgsel_window.set_transient_for(self.squarewindow)
        else:
            self.imgsel_window.set_transient_for(self.itemwindow)
        self.imgsel_area = self.get_widget('imgsel_area')
        self.imgsel_bgcolor_img = self.get_widget('bgcolor_img')
        self.imgsel_bgcolor_event = self.get_widget('bgcolor_event')
        self.imgsel_widget = widget
        self.imgsel_width = width
        self.imgsel_height = height
        self.imgsel_cols = cols
        self.imgsel_rows = rows
        self.imgsel_x = width*cols
        self.imgsel_y = height*rows
        self.imgsel_offset = offset
        self.imgsel_mousex = -1
        self.imgsel_mousey = -1
        self.imgsel_mousex_prev = -1
        self.imgsel_mousey_prev = -1
        self.imgsel_blank = None
        self.imgsel_getfunc = getfunc
        self.imgsel_getfunc_obj_func = getfunc_obj_func
        self.imgsel_getfunc_extraarg = None
        self.imgsel_pixbuffunc = None
        self.imgsel_init_bgcolor()
        req_width = self.imgsel_x+25
        req_height = 600
        if (self.imgsel_y < 580):
            req_height = self.imgsel_y + 20
        self.imgsel_window.set_size_request(req_width, req_height)
        self.imgsel_blank_color = self.imgsel_generate_grayscale(127)
        if (bgcolor_select):
            self.get_widget('imgsel_bgcolor_box').show()
        else:
            self.get_widget('imgsel_bgcolor_box').hide()
        self.imgsel_window.show()

    def imgsel_on_motion(self, widget, event):
        self.imgsel_mousex = int(event.x/self.imgsel_width)
        self.imgsel_mousey = int(event.y/self.imgsel_height)
        if (self.imgsel_mousex > self.imgsel_cols):
            self.imgsel_mousex = self.imgsel_cols
        if (self.imgsel_mousey > self.imgsel_rows):
            self.imgsel_mousey = self.imgsel_rows
        if (self.imgsel_mousex != self.imgsel_mousex_prev or
            self.imgsel_mousey != self.imgsel_mousey_prev):
            self.imgsel_clean.append((self.imgsel_mousex_prev, self.imgsel_mousey_prev))
            self.imgsel_clean.append((self.imgsel_mousex, self.imgsel_mousey))
            self.imgsel_mousex_prev = self.imgsel_mousex
            self.imgsel_mousey_prev = self.imgsel_mousey
        self.imgsel_area.queue_draw()

    def imgsel_draw(self, x, y):
        imgnum = (y*self.imgsel_cols)+x
        if (imgnum < 0 or imgnum > (self.imgsel_rows * self.imgsel_cols)):
            return
        if self.imgsel_getfunc_obj_func:
            loadnum = self.imgsel_getfunc_obj_func(imgnum+self.imgsel_offset)
        else:
            loadnum = imgnum+self.imgsel_offset
        if self.imgsel_getfunc_extraarg is not None:
            pixbuf = self.imgsel_getfunc(loadnum, None, True, self.imgsel_getfunc_extraarg)
        else:
            pixbuf = self.imgsel_getfunc(loadnum, None, True)
        if (self.imgsel_pixbuffunc is not None):
            pixbuf = self.imgsel_pixbuffunc(pixbuf)
        if (pixbuf is None):
            return
        self.imgsel_pixmap.draw_pixbuf(None, self.imgsel_blank, 0, 0, x*self.imgsel_width, y*self.imgsel_height)
        self.imgsel_pixmap.draw_pixbuf(None, pixbuf, 0, 0, x*self.imgsel_width, y*self.imgsel_height)
        if (x == self.imgsel_mousex and y == self.imgsel_mousey):
            color = self.imgsel_gc_white
        elif (x == self.imgsel_curx and y == self.imgsel_cury):
            color = self.imgsel_gc_green
        else:
            return

        # Outline points
        x1 = x*self.imgsel_width
        x2 = x1 + self.imgsel_width - 1
        x3 = x2
        x4 = x1
        x5 = x1

        y1 = y*self.imgsel_height
        y2 = y1
        y3 = y2 + self.imgsel_height - 1
        y4 = y3
        y5 = y1

        self.imgsel_pixmap.draw_lines(color, [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5)])
    
    def imgsel_generate_grayscale(self, color):
        return int((color<<24) + (color<<16) + (color<<8) + 255)

    def imgsel_on_expose(self, widget, event):
        if (self.imgsel_init):
            for (x, y) in self.imgsel_clean:
                self.imgsel_draw(x, y)
        else:
            if (int(self.imgsel_widget.get_value())-self.imgsel_offset < 0):
                self.imgsel_curx = -1
                self.imgsel_cury = -1
            else:
                self.imgsel_curx = (int(self.imgsel_widget.get_value())-self.imgsel_offset) % self.imgsel_cols
                self.imgsel_cury = int((int(self.imgsel_widget.get_value())-self.imgsel_offset) / self.imgsel_cols)
            self.imgsel_area.set_size_request(self.imgsel_x, self.imgsel_y)
            self.imgsel_pixmap = gtk.gdk.Pixmap(self.imgsel_area.window, self.imgsel_x, self.imgsel_y)
            self.imgsel_blank = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.imgsel_width, self.imgsel_height)
            self.imgsel_blank.fill(self.imgsel_blank_color)
            self.imgsel_gc_white = gtk.gdk.GC(self.imgsel_area.window)
            self.imgsel_gc_white.set_rgb_fg_color(gtk.gdk.Color(65535, 65535, 65535))
            self.imgsel_gc_black = gtk.gdk.GC(self.imgsel_area.window)
            self.imgsel_gc_black.set_rgb_fg_color(gtk.gdk.Color(0, 0, 0))
            self.imgsel_gc_green = gtk.gdk.GC(self.imgsel_area.window)
            self.imgsel_gc_green.set_rgb_fg_color(gtk.gdk.Color(0, 65535, 0))
            self.imgsel_pixmap.draw_rectangle(self.imgsel_gc_black, True, 0, 0, self.imgsel_x, self.imgsel_y)
            for y in range(self.imgsel_rows):
                for x in range(self.imgsel_cols):
                    self.imgsel_draw(x, y)
            self.imgsel_init = True
        self.imgsel_clean = []
        self.imgsel_area.window.draw_drawable(self.imgsel_area.get_style().fg_gc[gtk.STATE_NORMAL],
            self.imgsel_pixmap, 0, 0, 0, 0, self.imgsel_x, self.imgsel_y)

    def imgsel_on_clicked(self, widget, event):
        self.imgsel_init = False
        self.imgsel_widget.set_value(self.imgsel_mousex+(self.imgsel_cols*self.imgsel_mousey)+self.imgsel_offset)
        self.imgsel_window.hide()

    def on_bgcolor_img_clicked(self, widget, event):
        if self.have_numpy:
            try:
                pixels = self.imgsel_bgcolor_pixbuf.get_pixels_array()
            except (RuntimeError, ImportError):
                pixels = self.stupid_pixels_array(self.imgsel_bgcolor_pixbuf)
        else:
            pixels = self.stupid_pixels_array(self.imgsel_bgcolor_pixbuf)
        color = pixels[int(event.y)][int(event.x)][0]
        self.imgsel_blank_color = self.imgsel_generate_grayscale(color)
        self.imgsel_init = False
        self.imgsel_area.queue_draw()

    def get_gamedir_filelist(self, dir, ext, keepext=True, matchprefixes=None):
        if c.book == 1:
            path = os.path.join(self.prefs.get_str('paths', 'gamedir'), dir)
            files = os.listdir(path)
        else:
            files = []
            for file in self.gfx.filelist():
                (filedir, filename) = os.path.split(file)
                if filedir == dir:
                    files.append(filename)

        filelist = []
        ext = '.%s' % (ext)
        extlen = -len(ext)
        for file in files:
            if matchprefixes is not None:
                matched = False
                for prefix in matchprefixes:
                    if file[:len(prefix)] == prefix:
                        matched = True
                        break
                if not matched:
                    continue
            if file[extlen:] == ext:
                if (keepext):
                    filelist.append(file)
                else:
                    filelist.append(file[:extlen])
        filelist.sort()
        return filelist

    def populate_comboboxentry(self, boxname, list, blank=True):
        widget = self.get_widget(boxname)
        self.useful_comboboxentry(widget)
        if (blank):
            widget.append_text('')
        for item in list:
            widget.append_text(item)

    def stupid_pixels_array(self, buf):
        """
        An inefficient, stupid implementation of gtk.gdk.Pixbuf.get_pixels_array(),
        for systems whose PyGTK wasn't compiled with Numeric Array support.  Which
        includes the Windows PyGTK builds, otherwise I might not bother.

        Note that the array returned here is NOT identical to the one returned by
        get_pixels_array (to say nothing of being tied into the actual pixbuf, of
        course).  It merely replicates the structure well enough for our purposes
        that it's an acceptable substitute.
        """
        retarr = []
        pixels = buf.get_pixels()
        if (buf.get_has_alpha()):
            channels = 4
            packstr = 'BBBB'
        else:
            channels = 3
            packstr = 'BBB'
        idx = 0
        for y in range(buf.get_height()):
            retarr.append([])
            for x in range(buf.get_width()):
                retarr[y].append([])
                for color in unpack(packstr, pixels[idx:idx+channels]):
                    retarr[y][x].append(color)
                    # Old-style, which was more compatible at one point with get_pixels_array()
                    #retarr[y][x].append((color, 0))
                idx += channels
        return retarr

    def on_b2_item_attr3_treeview_clicked(self, widget, event):
        """
        For Book 2, we provide a TreeView showing various possible values
        for potions and reagents.  Double-clicking on an item will populate
        the value in the GUI; this handler takes care of that.
        """
        if event.type == gtk.gdk._2BUTTON_PRESS:
            (model, iter) = widget.get_selection().get_selected()
            self.get_widget('attr_modifier_3').set_value(model.get_value(iter, 1))
