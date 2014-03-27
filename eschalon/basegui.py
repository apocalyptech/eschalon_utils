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

class ImageSelWindow(gtk.Window):

    def __init__(self, object_tabs=False, on_clicked=None, on_motion=None, on_expose=None):
        super(ImageSelWindow, self).__init__()
        self.set_title("Select an Icon")
        self.set_modal(True)

        vbox = gtk.VBox()
        self.add(vbox)

        label = gtk.Label("Selecting an icon or hitting Escape will close this dialog.")
        label.set_alignment(.5, .5)
        label.set_padding(0, 6)
        vbox.pack_start(label, False, False)

        self.setup_drawing_area(vbox, on_clicked, on_motion, on_expose)

        self.bgcolor_box = gtk.VBox()
        vbox.pack_start(self.bgcolor_box, False, True)

        label = gtk.Label()
        label.set_markup('<i>(Click to change background color)</i>')
        label.set_alignment(.5, .5)
        label.set_padding(0, 2)
        self.bgcolor_box.pack_start(label, True, True)

        align = gtk.Alignment(.5, .5, 0, 1)
        self.bgcolor_box.pack_start(align, False, True)

        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_IN)
        align.add(vp)

        self.eventbox = gtk.EventBox()
        vp.add(self.eventbox)

        self.image = gtk.Image()
        self.image.set_alignment(.5, .5)
        self.image.set_padding(0, 0)
        self.image.set_size_request(170, 29)
        self.eventbox.add(self.image)

        self.connect('delete-event', self.delete_event)
        self.connect('key-release-event', self.key_release_event)

        vbox.show_all()

    def key_release_event(self, widget, event):
        """
        What to do when the user presses a key.  We're mostly
        looking for 'esc' so we can exit.
        """
        if gtk.gdk.keyval_name(event.keyval) == 'Escape':
            self.delete_event(None, None)

    def delete_event(self, widget, event):
        self.hide()
        return True

    def setup_drawing_area(self, vbox, on_clicked, on_motion, on_expose):
        (sw, self.drawingarea) = self.create_drawing_area(on_clicked, on_motion, on_expose)
        vbox.pack_start(sw, True, True)

    def create_drawing_area(self, on_clicked, on_motion, on_expose):
        """
        Creates a new DrawingArea, contained within a Viewport and ScrolledWindow.
        Returns a tuple of the ScrolledWindow and the DrawingArea.
        """

        sw = gtk.ScrolledWindow()

        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_IN)
        sw.add(vp)

        da = gtk.DrawingArea()
        da.set_events(gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK)
        if on_clicked is not None:
            da.connect('button-press-event', on_clicked)
        if on_motion is not None:
            da.connect('motion-notify-event', on_motion)
        if on_expose is not None:
            da.connect('expose-event', on_expose)
        vp.add(da)

        return (sw, da)


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
        self.prefs_savegame_b3 = self.prefsbuilder.get_object('savegame_b3_chooser')
        self.prefs_gamedir = self.prefsbuilder.get_object('gamedata_chooser')
        self.prefs_gamedir_b2 = self.prefsbuilder.get_object('gamedata_b2_chooser')
        self.prefs_gamedir_b3 = self.prefsbuilder.get_object('gamedata_b3_chooser')
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
            gfxfile = 'gfx.pak (or packedgraphics)'
        elif c.book == 2:
            gfxfile = 'datapak (or data)'
        elif c.book == 3:
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
                'on_item_singleval_changed_str': self.on_item_singleval_changed_str,
                'on_singleval_changed_int': self.on_singleval_changed_int,
                'on_item_singleval_changed_int': self.on_item_singleval_changed_int,
                'on_singleval_changed_int_itempic': self.on_singleval_changed_int_itempic,
                'on_singleval_changed_float': self.on_singleval_changed_float,
                'on_item_singleval_changed_float': self.on_item_singleval_changed_float,
                'on_dropdown_changed': self.on_dropdown_changed,
                'on_item_dropdown_changed': self.on_item_dropdown_changed,
                'on_category_dropdown_changed': self.on_category_dropdown_changed,
                'on_checkbox_changed': self.on_checkbox_changed,
                'on_item_checkbox_changed': self.on_item_checkbox_changed,
                'on_checkbox_bit_changed': self.on_checkbox_bit_changed,
                'on_modifier_changed': self.on_modifier_changed,
                'on_b2_bonus_changed': self.on_b2_bonus_changed,
                'on_item_close_clicked': self.on_item_close_clicked,
                'open_itemsel': self.open_itemsel,
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
        ### Image Selection Window
        ###
        self.imgsel_window = ImageSelWindow(
            on_clicked=self.imgsel_on_clicked,
            on_motion=self.imgsel_on_motion,
            on_expose=self.imgsel_on_expose)
        self.register_widget('item_imgsel_window', self.imgsel_window)

        ###
        ### Item Category and Subcategory dropdowns
        ###
        category_dd = self.get_widget('category')
        category_dd.get_model().clear()
        for category in c.categorytable.values():
            category_dd.append_text(category)
        subcategory_dd = self.get_widget('subcategory')
        subcategory_dd.get_model().clear()
        subcategory_dd.append_text('(none)')
        for subcategory in c.skilltable.values():
            subcategory_dd.append_text(subcategory)

        ###
        ### Item attribute modifier dropdowns
        ### Note that technically we don't need to do this dynamically, since
        ### these dropdowns only exist for Book 2.
        ###
        if book > 1:
            boxes = []
            for i in range(1, 4):
                boxes.append(self.get_widget('bonus_%d' % (i)))
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
            label = WrapLabel('<i>Note: Picture IDs in Book 2/3 are only '
                    'unique within their groups: armor, weapons, '
                    'magic/alchemy, or "other."</i>')
            label.show()
            align.add(label)

            align = self.get_widget('quantity_align_b23')
            label = WrapLabel('<i>(This value should always be greater than zero)</i>')
            label.show()
            align.add(label)

        ###
        ### Fix some tooltips
        ###
        if book == 1:
            self.get_widget('rarity').set_tooltip_text('This is generally 1 for ordinary items, and 3 for items which the character hasn\'t identified yet.  Other values\' meanings are unknown.');
            self.get_widget('quantity').set_tooltip_text('This value only makes sense when \'Can Stack\' is checked, above.  Ordinarily zero for items which can\'t be stacked.');
        else:
            self.get_widget('rarity').set_tooltip_text('This is 1 for items you\'ve identified - other numbers represent the difficulty of identifying the item.  Bar of Mithril is set to 9, for reference.')
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
        self.script_editor = ScriptEditor()
        self.setup_script_editor_launcher(self.get_widget('script_hbox'), self.get_widget('script'), self.window)

    def launch_script_editor(self, widget, script_entry, parent, has_coords=False):
        """
        Launches our script editor
        """
        res = self.script_editor.launch(script_entry.get_text(), parent, has_coords)
        if res == gtk.RESPONSE_OK:
            script_entry.set_text(self.script_editor.get_command_aggregate())

    def setup_script_editor_launcher(self, container, widget, parent, has_coords=False):
        """
        Adds a button to launch the script editor, given the container to put
        it in, and a widget whose .get_text() will provide the script text.
        """
        align = gtk.Alignment(0, .5, 1, 1)
        align.set_padding(0, 0, 6, 0)
        button = gtk.Button()
        button.add(gtk.image_new_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_BUTTON))
        button.set_tooltip_text('Launch Script Editor')
        button.connect('clicked', self.launch_script_editor, widget, parent, has_coords)
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
        return (os.path.isdir(os.path.join(self.prefsobj.get_str('paths', 'gamedir'), 'packedgraphics'))) or (os.path.isfile(os.path.join(self.prefsobj.get_str('paths', 'gamedir'), 'gfx.pak')))

    def gamedir_set_b2(self):
        return (os.path.isdir(os.path.join(self.prefsobj.get_str('paths', 'gamedir_b2'), 'data'))) or (os.path.isfile(os.path.join(self.prefsobj.get_str('paths', 'gamedir_b2'), 'datapak')))

    def gamedir_set_b3(self):
        return (os.path.isfile(os.path.join(self.prefsobj.get_str('paths', 'gamedir_b3'), 'datapak')))

    def gamedir_set(self, book=None):
        if book is None:
            if c.book == 1:
                return self.gamedir_set_b1()
            elif c.book == 2:
                return self.gamedir_set_b2()
            elif c.book == 3:
                return self.gamedir_set_b3()
        else:
            if book == 1:
                return self.gamedir_set_b1()
            elif c.book == 2:
                return self.gamedir_set_b2()
            elif c.book == 3:
                return self.gamedir_set_b3()

    def get_savegame_dir_key(self):
        if c.book == 1:
            return 'savegames'
        elif c.book == 2:
            return 'savegames_b2'
        elif c.book == 3:
            return 'savegames_b3'

    def get_gamedir_key(self):
        if c.book == 1:
            return 'gamedir'
        elif c.book == 2:
            return 'gamedir_b2'
        elif c.book == 3:
            return 'gamedir_b3'

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
            self.prefsbuilder.get_object('b3_dir_tab').hide()
            gui_gamedir = self.prefs_gamedir
            gui_savegamedir = self.prefs_savegame
            look_for = [ 'gfx.pak', 'packedgraphics' ]
        elif c.book == 2:
            self.prefsbuilder.get_object('b1_dir_tab').hide()
            self.prefsbuilder.get_object('b2_dir_tab').show()
            self.prefsbuilder.get_object('b3_dir_tab').hide()
            gui_gamedir = self.prefs_gamedir_b2
            gui_savegamedir = self.prefs_savegame_b2
            look_for = [ 'datapak', 'data' ]
        elif c.book == 3:
            self.prefsbuilder.get_object('b1_dir_tab').hide()
            self.prefsbuilder.get_object('b2_dir_tab').hide()
            self.prefsbuilder.get_object('b3_dir_tab').show()
            gui_gamedir = self.prefs_gamedir_b3
            gui_savegamedir = self.prefs_savegame_b3
            look_for = [ 'datapak' ]

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
        self.prefs_warn_slowzip.set_active(self.prefsobj.get_bool('mapgui', 'warn_slow_zip'))
        #self.prefsnotebook.set_current_page(0)
        self.prefswindow.set_transient_for(self.window)
        response = self.prefswindow.run()
        self.prefswindow.hide()
        if (response == gtk.RESPONSE_OK):
            self.prefsobj.set_int('mapgui', 'default_zoom', int(self.prefs_default_zoom.get_value()))
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
            found = False
            for i in look_for:
                if os.path.exists(os.path.join(new_gamedir, i)):
                    found = True
            if (cur_gamedir != '' or found):
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
        if (self.curitemcategory == self.ITEM_EQUIP):
            obj = self.char.__dict__[self.curitem]
            origobj = self.origchar.__dict__[self.curitem]
        elif (self.curitemcategory == self.ITEM_INV):
            obj = self.char.inventory[self.curitem[0]][self.curitem[1]]
            origobj = self.origchar.inventory[self.curitem[0]][self.curitem[1]]
        elif (self.curitemcategory == self.ITEM_READY):
            obj = self.char.readyitems[self.curitem]
            origobj = self.origchar.readyitems[self.curitem]
        elif (self.curitemcategory == self.ITEM_MAP):
            obj = self.map.tiles[self.tile_y][self.tile_x].tilecontents[self.curitem[1]].items[self.curitem[0]]
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
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_item_singleval_changed_str(self, widget):
        """ What to do when a string value changes on the item edit screen. """
        self.on_singleval_changed_str(widget)
        if widget.get_text() != '':
            (obj, origobj) = self.get_comp_objects()
            self.set_item_quantity_nonzero(obj)

    def on_singleval_changed_int(self, widget):
        """ What to do when an int value changes. """
        wname = widget.get_name()
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = int(widget.get_value())
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_item_singleval_changed_int(self, widget):
        """ What to do when an int value changes on our item screen. """
        self.on_singleval_changed_int(widget)
        if widget.get_name() != 'quantity' and int(widget.get_value()) > 0:
            (obj, origobj) = self.get_comp_objects()
            self.set_item_quantity_nonzero(obj)

    def on_singleval_changed_float(self, widget):
        """ What to do when an int value changes. """
        wname = widget.get_name()
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_value()
        # Note that for floats, we shouldn't do exact precision, hence the 1e-6 comparison here.
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((abs(origobj.__dict__[wname] - obj.__dict__[wname])<1e-6), wname, labelwidget, label)

    def on_item_singleval_changed_float(self, widget):
        """ What to do when an int value changes on our item screen. """
        self.on_singleval_changed_float(widget)
        if widget.get_value() > .000001 or widget.get_value() < -.000001:
            (obj, origobj) = self.get_comp_objects()
            self.set_item_quantity_nonzero(obj)

    def update_itempic_image(self):
        if (self.gfx is not None):
            (obj, origobj) = self.get_comp_objects()
            self.get_widget('item_pic_image').set_from_pixbuf(self.gfx.get_item(obj))

    def on_singleval_changed_int_itempic(self, widget):
        """ Special-case to handle changing the item picture properly. """
        self.on_item_singleval_changed_int(widget)
        self.update_itempic_image()

    def set_item_quantity_nonzero(self, item):
        """
        Books II and III will exhibit strange behavior if an item's quantity is set to zero, and
        requiring the user to set it every time would be annoying.  This will set the quantity
        to 1 if we're passed an item object with a quantity of zero.
        """
        if c.book > 1 and item.quantity == 0:
            self.get_widget('quantity').set_value(1)

    def on_dropdown_changed(self, widget):
        """ What to do when a dropdown is changed """
        wname = widget.get_name()
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_active()
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)
    
    def on_item_dropdown_changed(self, widget):
        """ What to do when a dropdown changes on our item screen """
        self.on_dropdown_changed(widget)
        if widget.get_active() != 0:
            (obj, origobj) = self.get_comp_objects()
            self.set_item_quantity_nonzero(obj)
    
    def on_category_dropdown_changed(self, widget):
        """
        What to do when the item category dropdown is changed.
        Only has an actual effect in Book 2, though technically Book 1 will go through
        the motions as well.
        """
        self.on_item_dropdown_changed(widget)
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
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_item_checkbox_changed(self, widget):
        """ What to do when a regular checkbox changes on our item edit screen. """
        self.on_checkbox_changed(widget)
        if widget.get_active():
            (obj, origobj) = self.get_comp_objects()
            self.set_item_quantity_nonzero(obj)

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
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(wname)
            self.set_changed_widget((origobj.__dict__[shortname] & mask == obj.__dict__[shortname] & mask), wname, labelwidget, label)

    def on_modifier_changed(self, widget):
        """ What to do when our attr or skill modifier changes. """
        wname = widget.get_name()
        (which, category) = wname.rsplit('_', 1)
        modifiertext = '%s_modifier' % (which)
        modifiedtext = '%s_modified' % (which)
        modifier = int(self.get_widget(modifiertext).get_value())
        modified = self.get_widget(modifiedtext).get_active()
        (obj, origobj) = self.get_comp_objects()
        if (wname == modifiertext):
            obj.__dict__[modifiertext] = modifier
        elif (wname == modifiedtext):
            obj.__dict__[modifiedtext] = modified
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(which)
            self.set_changed_widget((origobj.__dict__[modifiertext] == obj.__dict__[modifiertext] and
                origobj.__dict__[modifiedtext] == obj.__dict__[modifiedtext]), which, labelwidget, label)

    def on_b2_bonus_changed(self, widget):
        """ What to do when a book 2 item attribute changes. """
        if c.book == 1:
            return
        wname = widget.get_name()
        num = int(wname.split('_')[-1])
        bonusvaluetext = 'bonus_value_%d' % (num)
        bonustext = 'bonus_%d' % (num)
        bonusvalue = int(self.get_widget(bonusvaluetext).get_value())
        bonus = self.get_widget(bonustext).get_active()
        (obj, origobj) = self.get_comp_objects()
        if (wname == bonusvaluetext):
            obj.__dict__[bonusvaluetext] = bonusvalue
        elif (wname == bonustext):
            obj.__dict__[bonustext] = bonus
        if num == 3:
            if obj.bonus_value_3 < 0:
                self.get_widget('bonus_plusminus_3').set_text('')
            else:
                self.get_widget('bonus_plusminus_3').set_text('+')
        if (self.curitemcategory != self.ITEM_MAP):
            (labelwidget, label) = self.get_label_cache(bonusvaluetext)
            self.set_changed_widget((origobj.__dict__[bonusvaluetext] == obj.__dict__[bonusvaluetext] and
                origobj.__dict__[bonustext] == obj.__dict__[bonustext]), bonusvaluetext, labelwidget, label)

    def on_item_close_clicked(self, widget=None, event=None, dohide=True):
        if (self.curitemcategory == self.ITEM_EQUIP):
            self.populate_equip_button(self.curitem)
        elif (self.curitemcategory == self.ITEM_INV):
            self.populate_inv_button(self.curitem[0], self.curitem[1])
        elif (self.curitemcategory == self.ITEM_READY):
            self.populate_ready_button(self.curitem)
        elif (self.curitemcategory == self.ITEM_MAP):
            self.populate_mapitem_button(self.curitem[0], self.curitem[1])
        if (self.curitemcategory != self.ITEM_MAP):
            for name in self.itemchanged.keys():
                (labelwidget, label) = self.get_label_cache(name)
                self.set_changed_widget(True, name, labelwidget, label, False)
            self.itemchanged = {}
            self.curitemcategory = self.ITEM_NONE
        if (dohide):
            self.itemwindow.hide()
        return True

    def populate_item_button(self, item, widget, imgwidget, tablewidget):
        str = ''
        if (item.item_name == ''):
            str = '<i>(None)</i>'
        elif (item.category == 0):
            str = '<i>%s (no Category specified)</i>' % (item.item_name)
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
        self.get_widget('category').set_active(item.category)
        self.get_widget('subcategory').set_active(item.subcategory)
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
            self.get_widget('duration').set_value(item.duration)
            self.get_widget('zero1').set_value(item.zero1)
            self.get_widget('emptystr').set_text(item.emptystr)
        else:
            self.get_widget('cur_hp').set_value(item.cur_hp)
            self.get_widget('max_hp').set_value(item.max_hp)
            self.get_widget('bonus_1').set_active(item.bonus_1)
            self.get_widget('bonus_value_1').set_value(item.bonus_value_1)
            self.get_widget('bonus_2').set_active(item.bonus_2)
            self.get_widget('bonus_value_2').set_value(item.bonus_value_2)
            self.get_widget('bonus_3').set_active(item.bonus_3)
            self.get_widget('bonus_value_3').set_value(item.bonus_value_3)
            self.get_widget('quest').set_value(item.quest)
            self.get_widget('material').set_value(item.material)
            self.get_widget('spell').set_text(item.spell)
            self.get_widget('spell_power').set_value(item.spell_power)
            if (item.is_projectile):
                self.get_widget('is_projectile').set_active(True)
            else:
                self.get_widget('is_projectile').set_active(False)

        self.get_widget('rarity').set_value(item.rarity)
        if (item.canstack):
            self.get_widget('canstack').set_active(True)
        else:
            self.get_widget('canstack').set_active(False)
        self.get_widget('quantity').set_value(item.quantity)
        self.get_widget('script').set_text(item.script)

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
            dropdownvals = [ 'category', 'subcategory', 'incr' ]
            intvals = [ 'value', 'basedamage', 'basearmor',
                    'hitpoint', 'mana', 'tohit', 'damage', 'armor',
                    'rarity', 'duration', 'quantity', 'zero1' ]
            floatvals = [ 'weight' ]
            checkboxvals = [ 'canstack' ]
            checkboxbitvals = [ 'flags_0003' ]
            modifiervals = [ 'attr_modifier', 'skill_modifier' ]
            b2modifiervals = [ ]
        else:
            strvals = [ 'item_name', 'script', 'spell' ]
            dropdownvals = [ 'category', 'subcategory' ]
            intvals = [ 'value', 'basedamage', 'basearmor',
                    'rarity', 'quantity',
                    'cur_hp', 'max_hp',
                    'quest', 'material', 'spell_power' ]
            floatvals = [ 'weight' ]
            checkboxvals = [ 'canstack', 'is_projectile' ]
            checkboxbitvals = [ ]
            modifiervals = [ ]
            b2modifiervals = [ 'bonus_value_1', 'bonus_value_2', 'bonus_value_3' ]
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
            self.on_b2_bonus_changed(self.get_widget(val))
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
        (x, y) = self.imgsel_window.image.get_size_request()
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
        self.imgsel_window.eventbox.connect('button-press-event', self.on_bgcolor_img_clicked)
        self.imgsel_window.image.set_from_pixbuf(pixbuf)
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
        self.imgsel_window = self.get_widget("item_imgsel_window")
        if (self.curitemcategory == self.ITEM_MAP):
            self.imgsel_window.set_transient_for(self.tilewindow)
        else:
            self.imgsel_window.set_transient_for(self.itemwindow)
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
            self.imgsel_window.bgcolor_box.show()
        else:
            self.imgsel_window.bgcolor_box.hide()
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
        self.imgsel_window.drawingarea.queue_draw()

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
            self.imgsel_window.drawingarea.set_size_request(self.imgsel_x, self.imgsel_y)
            self.imgsel_pixmap = gtk.gdk.Pixmap(self.imgsel_window.drawingarea.window, self.imgsel_x, self.imgsel_y)
            self.imgsel_blank = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.imgsel_width, self.imgsel_height)
            self.imgsel_blank.fill(self.imgsel_blank_color)
            self.imgsel_gc_white = gtk.gdk.GC(self.imgsel_window.drawingarea.window)
            self.imgsel_gc_white.set_rgb_fg_color(gtk.gdk.Color(65535, 65535, 65535))
            self.imgsel_gc_black = gtk.gdk.GC(self.imgsel_window.drawingarea.window)
            self.imgsel_gc_black.set_rgb_fg_color(gtk.gdk.Color(0, 0, 0))
            self.imgsel_gc_green = gtk.gdk.GC(self.imgsel_window.drawingarea.window)
            self.imgsel_gc_green.set_rgb_fg_color(gtk.gdk.Color(0, 65535, 0))
            self.imgsel_pixmap.draw_rectangle(self.imgsel_gc_black, True, 0, 0, self.imgsel_x, self.imgsel_y)
            for y in range(self.imgsel_rows):
                for x in range(self.imgsel_cols):
                    self.imgsel_draw(x, y)
            self.imgsel_init = True
        self.imgsel_clean = []
        self.imgsel_window.drawingarea.window.draw_drawable(self.imgsel_window.drawingarea.get_style().fg_gc[gtk.STATE_NORMAL],
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
        self.imgsel_window.drawingarea.queue_draw()

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
            self.get_widget('bonus_value_3').set_value(model.get_value(iter, 1))
