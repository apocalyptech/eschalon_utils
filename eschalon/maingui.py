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

# Load GTK Deps
try:
    import gtk
except Exception, e:
    print 'Python GTK Modules not found: %s' % (str(e))
    print 'Hit enter to exit...'
    sys.stdin.readline()
    sys.exit(1)

# Load in our Cairo dep
try:
    import cairo
except Exception, e:
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK)
    dialog.set_markup('PyCairo could not be loaded: %s' % (str(e)))
    dialog.run()
    dialog.destroy()
    sys.exit(1)

# Check for minimum GTK+ version
if (gtk.check_version(2, 18, 0) is not None):
    dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK)
    dialog.set_markup('<b>Note:</b> The minimum required version of gtk+ is <i>probably</i> 2.18.0, though it\'s possible it will work on some older versions.  You\'re welcome to continue, but know that you may encounter weird behavior.')
    dialog.run()
    dialog.destroy()

# Lookup tables we'll need
from eschalon.gfx import Gfx
from eschalon.basegui import BaseGUI
from eschalon.character import Character, B1Character, B2Character
from eschalon.item import Item, B1Item, B2Item
from eschalon.savefile import LoadException
from eschalon import constants as c
from eschalon import app_name, version, url, authors

class MainGUI(BaseGUI):

    def __init__(self, options, prefs, req_book):
        self.options = options
        self.prefs = prefs
        self.path_init()
        self.req_book = req_book
        c.switch_to_book(req_book)

    def run(self):

        # Some vars we need regardless of whether we have a file or not
        self.widgetcache = {}

        # We need this because Not Everything's in Glade anymore
        # Note that we have a couple of widget caches now, so those should
        # be consolidated
        self.fullwidgetcache = {}

        # Let's make sure that char exists, too
        self.char = None

        # Start up our GUI
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.datafile('maingui.ui'))
        self.builder.add_from_file(self.datafile('itemgui.ui'))
        self.window = self.get_widget('mainwindow')
        self.itemwindow = self.get_widget('itemwindow')
        self.itemwindow.set_transient_for(self.window)
        self.loadwindow = self.get_widget('loadwindow')
        self.aboutwindow = self.get_widget('aboutwindow')
        self.mainbook = self.get_widget('mainbook')
        self.itemsel = self.get_widget('itemselwindow')
        self.avatarsel = self.get_widget('avatarselwindow')
        if (self.window):
            self.window.connect('destroy', gtk.main_quit)

        # Explicitly set our widget names (needed for gtk+ 2.20 compatibility)
        # See https://bugzilla.gnome.org/show_bug.cgi?id=591085
        for object in self.builder.get_objects():
            try:
                builder_name = gtk.Buildable.get_name(object)
                if builder_name:
                    object.set_name(builder_name)
            except TypeError:
                pass

        # Register ComboBoxEntry child objects since the new Glade doesn't
        comboboxentries = ['origin', 'axiom', 'classname']
        spellboxentries = []
        readyentries = ['readied_spell']
        for i in range(10):
            spellboxentries.append('readyslots_spell_%d' % (i))
        for var in comboboxentries + spellboxentries + readyentries:
            self.register_widget(var, self.get_widget('%s_box' % (var)).child)
        for var in comboboxentries:
            self.get_widget(var).connect('changed', self.on_singleval_changed_str)
        for var in spellboxentries:
            self.get_widget(var).connect('changed', self.on_readyslots_changed)
        for var in readyentries:
            self.get_widget(var).connect('changed', self.on_cur_ready_changed)

        # GUI additions
        self.gui_finish()

        # Avatar Selection Window extras
        self.avatarsel_init = False
        self.avatarsel_clean = []
        self.avatarsel_area = self.get_widget('avatarsel_area')
        self.avatarsel_x = 480
        self.avatarsel_y = 60
        self.avatarsel_cols = 8
        self.avatarsel_rows = 1
        self.avatarsel_width = 60
        self.avatarsel_height = 60
        self.avatarsel_mousex = -1
        self.avatarsel_mousey = -1
        self.avatarsel_mousex_prev = -1
        self.avatarsel_mousey_prev = -1

        # Set up our graphics cache
        self.prefs_init(self.prefs)
        if self.req_book == 1:
            self.optional_gfx()
        if (self.gamedir_set() and self.req_book == 1):
            self.gfx = Gfx(self.prefs, self.datadir)
        else:
            self.gfx = None
        self.assert_gfx_buttons()

        # Dictionary of signals.
        dic = { 'gtk_main_quit': self.gtk_main_quit,
                'on_revert': self.on_revert,
                'on_load': self.on_load,
                'on_about': self.on_about,
                'on_save_as': self.on_save_as,
                'on_prefs': self.on_prefs,
                'save_char': self.save_char,
                'on_fxblock_button_clicked': self.on_fxblock_button_clicked,
                'on_checkbox_arr_changed': self.on_checkbox_arr_changed,
                'on_readyslots_changed': self.on_readyslots_changed,
                'on_cur_ready_changed': self.on_cur_ready_changed,
                'on_multarray_changed': self.on_multarray_changed,
                'on_multarray_text_changed': self.on_multarray_text_changed,
                'on_multarray_changed_fx': self.on_multarray_changed_fx,
                'on_portal_loc_changed': self.on_portal_loc_changed,
                'on_singleval_changed_int_avatar': self.on_singleval_changed_int_avatar,
                'on_dropdownplusone_changed': self.on_dropdownplusone_changed,
                'on_dropdownplusone_changed_b2': self.on_dropdownplusone_changed_b2,
                'open_avatarsel': self.open_avatarsel,
                'avatarsel_on_motion': self.avatarsel_on_motion,
                'avatarsel_on_expose': self.avatarsel_on_expose,
                'avatarsel_on_clicked': self.avatarsel_on_clicked,
                'on_b2picid_changed': self.on_b2picid_changed
                }
        dic.update(self.item_signals())
        # Really we should only attach the signals that will actually be sent, but this
        # should be fine here, anyway.
        self.builder.connect_signals(dic)

        # Set up the statusbar
        self.statusbar = self.get_widget('mainstatusbar')
        self.sbcontext = self.statusbar.get_context_id('Main Messages')

        # If we were given a filename, load it.  If not, display the load dialog
        if (self.options['filename'] == None):
            if (not self.on_load()):
                return
        else:
            if (not self.load_from_file(self.options['filename'])):
                if (not self.on_load()):
                    return

        # Start the main gtk loop
        self.window.show()
        gtk.main()

    def assert_gfx_buttons(self):
        """
        Small routine to ensure that we're drawing the right stuff
        depending on if we can read our graphics file or not.
        """
        if (self.gamedir_set()):
            self.get_widget('picid_button').show()
            self.get_widget('itemgui_picid_button').show()
        else:
            self.get_widget('picid_button').hide()
            self.get_widget('itemgui_picid_button').hide()

    def on_prefs(self, widget):
        """ Override on_prefs a bit. """
        (changed, alert_changed) = super(MainGUI, self).on_prefs(widget)
        if (changed and alert_changed):
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK)
            dialog.set_transient_for(self.window)
            dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            dialog.set_markup('<b>Note:</b> Changes to graphics may not immediately update upon changing.  To ensure that your new settings are completely enabled, please quit and restart the application.')
            dialog.run()
            dialog.destroy()
        self.assert_gfx_buttons()
        if (changed and self.gamedir_set()):
            self.gfx = Gfx(self.prefs, self.datadir)

    # Use this to display the loading dialog, and deal with the main window accordingly
    def on_load(self, widget=None):
        
        # Blank out the main area
        self.mainbook.set_sensitive(False)

        # Create the dialog
        dialog = gtk.FileChooserDialog('Open New Character File...', None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

        # Figure out what our initial path should be
        path = ''
        if (self.char == None):
            # This will only happen during the initial load
            path = self.get_current_savegame_dir()
        else:
            path = os.path.dirname(os.path.realpath(self.char.df.filename))

        # Set the initial path
        if (path and path != '' and os.path.isdir(path)):
            dialog.set_current_folder(path)

        filter = gtk.FileFilter()
        filter.set_name("Character Files")
        filter.add_pattern("char")
        filter.add_pattern("char.*")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        # Run the dialog and process its return values
        rundialog = True
        while (rundialog):
            rundialog = False
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                if (not self.load_from_file(dialog.get_filename())):
                    rundialog = True
            else:
                # Check to see if this was the initial load, started without a filename
                if (self.char == None):
                    return False

        # Clean up
        dialog.destroy()
        self.mainbook.set_sensitive(True)

        return True

    # Show the Save As dialog
    def on_save_as(self, widget=None):

        # Blank out the main area
        self.mainbook.set_sensitive(False)

        # Create the dialog
        dialog = gtk.FileChooserDialog('Save Character File...', None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE_AS, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.set_do_overwrite_confirmation(True)
        if (self.char != None):
            path = os.path.dirname(os.path.realpath(self.char.df.filename))
            if (path != ''):
                dialog.set_current_folder(path)

        filter = gtk.FileFilter()
        filter.set_name("Character Files")
        filter.add_pattern("char")
        filter.add_pattern("char.*")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        # Run the dialog and process its return values
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.char.df.filename = dialog.get_filename()
            self.save_char()
            self.putstatus('Saved as %s' % (self.char.df.filename))
            self.get_widget('saveaswindow').run()
            self.get_widget('saveaswindow').hide()

        # Clean up
        dialog.destroy()
        self.mainbook.set_sensitive(True)

    # Show the About dialog
    def on_about(self, widget):
        global app_name, version, url, authors

        about = self.get_widget('aboutwindow')

        # If the object doesn't exist in our cache, create it
        if (about == None):
            about = gtk.AboutDialog()
            about.set_transient_for(self.window)
            about.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            about.set_name(app_name)
            about.set_version(version)
            about.set_website(url)
            about.set_authors(authors)
            licensepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'COPYING.txt')
            if (os.path.isfile(licensepath)):
                try:
                    df = open(licensepath, 'r')
                    about.set_license(df.read())
                    df.close()
                except:
                    pass
            iconpath = self.datafile('eb1_icon_64.png')
            if (os.path.isfile(iconpath)):
                try:
                    about.set_logo(gtk.gdk.pixbuf_new_from_file(iconpath))
                except:
                    pass
            self.register_widget('aboutwindow', about, False)

        # Show the about dialog
        self.mainbook.set_sensitive(False)
        about.run()
        about.hide()
        self.mainbook.set_sensitive(True)

    # Use this to load in a character from a file
    def load_from_file(self, filename):

        # Load the file, if we can
        try:
            char = Character.load(filename, None, self.req_book)
            char.read()
        except LoadException, e:
            errordiag = self.get_widget('loaderrorwindow')
            self.get_widget('loaderror_textview').get_buffer().set_text(e.text)
            errordiag.run()
            errordiag.hide()
            return False

        # Basic vars
        self.origchar = char
        self.char = char.replicate()
        self.labelcache = {}
        self.changed = {}

        # Support for our item screens
        self.curitemtype = self.ITEM_NONE
        self.curitem = ''
        self.itemchanged = {}
        self.itemclipboard = None

        # Update our status bar
        self.putstatus('Editing ' + self.char.df.filename)

        # Load information from the character
        self.populate_form_from_char()

        # Load default dropdowns, since Glade apparently can't
        self.get_widget('fxblock_dropdown').set_active(0)

        # ... and switch over to the initial pages of our notebooks
        self.mainbook.set_current_page(0)
        self.get_widget('itemnotebook').set_current_page(0)
        self.get_widget('invnotebook').set_current_page(0)

        # Return success
        return True

    def putstatus(self, text):
        """ Pushes a message to the status bar """
        self.statusbar.push(self.sbcontext, text)

    def get_label_cache(self, name):
        """ Returns a widget and the proper label for the widget (to save on processing) """
        if (not self.labelcache.has_key(name)):
            widget = self.get_widget(name + '_label')
            self.widgetcache[name] = widget
            self.labelcache[name] = widget.get_label()
        return (self.widgetcache[name], self.labelcache[name])

    def register_widget(self, name, widget, doname=True):
        if doname:
            widget.set_name(name)
        self.fullwidgetcache[name] = widget

    def get_widget(self, name):
        """ Returns a widget from our cache, or from builder obj if it's not present in the cache. """
        if (not self.fullwidgetcache.has_key(name)):
            self.register_widget(name, self.builder.get_object(name), False)
        return self.fullwidgetcache[name]

    def check_item_changed(self):
        """
        Check to see if our item is changed, and if so, do the appropriate thing on the main form.
        """
        if self.curitemtype == self.ITEM_EQUIP:
            (labelwidget, label) = self.get_label_cache(self.curitem)
            labelname = labelwidget.get_name()
            (labelname, foo) = labelname.rsplit('_', 1)
            self.set_changed_widget((len(self.itemchanged) == 0), labelname, labelwidget, label, False)
        elif self.curitemtype == self.ITEM_INV:
            labelname = 'inv_%d_%d' % (self.curitem[0], self.curitem[1])
            (labelwidget, label) = self.get_label_cache(labelname)
            self.set_changed_widget((len(self.itemchanged) == 0), labelname, labelwidget, label, False)
        elif self.curitemtype == self.ITEM_READY:
            labelname = 'ready_%d' % (self.curitem)
            (labelwidget, label) = self.get_label_cache(labelname)
            self.set_changed_widget((len(self.itemchanged) == 0), labelname, labelwidget, label, False)
        else:
            pass

    def set_changed_widget(self, unchanged, name, labelwidget, label, doitem=True):
        """ Mark a label as changed or unchanged, on the GUI. """
        if (unchanged):
            if (not doitem or self.curitemtype == self.ITEM_NONE):
                if self.changed.has_key(name):
                    del self.changed[name]
            else:
                if self.itemchanged.has_key(name):
                    del self.itemchanged[name]
                self.check_item_changed()
            return labelwidget.set_markup(label)
        else:
            if (not doitem or self.curitemtype == self.ITEM_NONE):
                self.changed[name] = True
            else:
                self.itemchanged[name] = True
                self.check_item_changed()
            return labelwidget.set_markup('<span foreground="red">' + label + '</span>')

    def has_unsaved_changes(self):
        return (len(self.changed.keys()) > 0)

    def clear_all_changes(self):
        """ Clear out all the 'changed' notifiers on the GUI (used mostly just when saving). """
        # We'll have to make a copy of the dict on account of objectness
        mychanged = []
        for name in self.changed.keys():
            mychanged.append(name)
        for name in mychanged:
            (labelwidget, label) = self.get_label_cache(name)
            self.set_changed_widget(True, name, labelwidget, label)

    def on_singleval_changed_int_avatar(self, widget):
        """ Special-case to handle changing the avatar picture properly. """
        self.on_singleval_changed_int(widget)
        if (self.get_widget('picid').get_value_as_int() % 256 == 0):
            if (self.gfx is None):
                self.get_widget('picid_image').set_from_stock(gtk.STOCK_EDIT, 4)
            else:
                pixbuf = self.gfx.get_avatar(widget.get_value_as_int()/256)
                if (pixbuf is None):
                    self.get_widget('picid_image').set_from_stock(gtk.STOCK_EDIT, 4)
                else:
                    self.get_widget('picid_image').set_from_pixbuf(self.gfx.get_avatar(widget.get_value_as_int()/256))
        else:
            self.get_widget('picid_image').set_from_stock(gtk.STOCK_EDIT, 4)
    
    def on_dropdownplusone_changed(self, widget):
        """ What to do when a dropdown is changed, when our index starts at 1.  """
        wname = widget.get_name()
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_active() + 1
        self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)
    
    def on_dropdownplusone_changed_b2(self, widget):
        """
        What to do when a dropdown is changed, when our index starts at 1.
        Also, the GUI elements in question will be prefixed with "b2"
        """
        wname = widget.get_name()
        objwname = wname[2:]
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[objwname] = widget.get_active() + 1
        self.set_changed_widget((origobj.__dict__[objwname] == obj.__dict__[objwname]), wname, labelwidget, label)

    def on_b2picid_changed(self, widget):
        """
        Custom handling for the Book 2 Picture ID field
        """
        wname = widget.get_name()
        objwname = wname[2:]
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        if (widget.get_active() == 12):
            obj.__dict__[objwname] = 0xFFFFFFFF
        else:
            obj.__dict__[objwname] = widget.get_active() + 1
        self.set_changed_widget((origobj.__dict__[objwname] == obj.__dict__[objwname]), wname, labelwidget, label)

    def on_portal_loc_changed(self, widget):
        """ What to do when one of our bound-portal locations changes. """
        wname = widget.get_name()
        (shortwname, num) = wname.rsplit('_', 1)
        num = int(num)
        basename = 'portal_loc_%d' % (num)
        (labelwidget, label) = self.get_label_cache(basename)
        (obj, origobj) = self.get_comp_objects()
        if shortwname == 'portal_loc_loc':
            obj.portal_locs[num][0] = int(widget.get_value())
        elif shortwname == 'portal_loc_map':
            obj.portal_locs[num][1] = widget.get_text()
        elif shortwname == 'portal_loc_mapeng':
            obj.portal_locs[num][2] = widget.get_text()
        changed = False
        for i in range(3):
            if obj.portal_locs[num][i] != origobj.portal_locs[num][i]:
                changed = True
                break
        self.set_changed_widget(not changed, basename, labelwidget, label)

    def on_effect_changed(self, widget):
        """ What to do when our effect value changes.  Slightly different from Books 1 and 2"""
        wname = widget.get_name()
        (shortname, arrnum) = wname.rsplit('_', 1)
        arrnum = int(arrnum)
        labelname = 'statuses_%d' % (arrnum)
        (labelwidget, label) = self.get_label_cache(labelname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[shortname][arrnum] = int(widget.get_value())
        changed = (origobj.statuses[arrnum] != obj.statuses[arrnum])
        if c.book == 2 and (origobj.statuses_extra[arrnum] != obj.statuses_extra[arrnum]):
            changed = True
        self.set_changed_widget(not changed, labelname, labelwidget, label)

    def on_multarray_text_changed(self, widget):
        """ What to do when a string value changes in an array. """
        wname = widget.get_name()
        (shortname, arrnum) = wname.rsplit('_', 1)
        arrnum = int(arrnum)
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[shortname][arrnum] = widget.get_text()
        self.set_changed_widget((origobj.__dict__[shortname][arrnum] == obj.__dict__[shortname][arrnum]), wname, labelwidget, label)

    def on_multarray_changed(self, widget):
        """ What to do when an int value changes in an array. """
        wname = widget.get_name()
        (shortname, arrnum) = wname.rsplit('_', 1)
        arrnum = int(arrnum)
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        # TODO: report the bug here - widget.get_value_as_int() returns a signed value...
        obj.__dict__[shortname][arrnum] = int(widget.get_value())
        self.set_changed_widget((origobj.__dict__[shortname][arrnum] == obj.__dict__[shortname][arrnum]), wname, labelwidget, label)

    def on_checkbox_arr_changed(self, widget):
        """ What to do when a checkbox changes, and it's in an array. """
        wname = widget.get_name()
        if (widget.get_active()):
            val = 1
        else:
            val = 0
        (shortname, arrnum) = wname.rsplit('_', 1)
        arrnum = int(arrnum)
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[shortname][arrnum] = val
        self.set_changed_widget((origobj.__dict__[shortname][arrnum] == obj.__dict__[shortname][arrnum]), wname, labelwidget, label)

    def on_cur_ready_changed(self, widget):
        """ What to do when our currently-readied spell changes (only on Book 2). """
        (obj, origobj) = self.get_comp_objects()
        if obj.book == 1:
            return
        (labelwidget, label) = self.get_label_cache('readied_spell')
        obj.readied_spell = self.get_widget('readied_spell').get_text()
        obj.readied_spell_lvl = self.get_widget('readied_spell_lvl').get_value_as_int()
        self.set_changed_widget((origobj.readied_spell == obj.readied_spell) and
            (origobj.readied_spell_lvl == obj.readied_spell_lvl), 'readied_spell', labelwidget, label)

    def on_readyslots_changed(self, widget):
        """ What to do when one of our readied-spell slots changes. """
        wname = widget.get_name()
        (foo, slotnum) = wname.rsplit('_', 1)
        slotnum = int(slotnum)
        spell = self.get_widget('readyslots_spell_%d' % (slotnum)).get_text()
        level = self.get_widget('readyslots_level_%d' % (slotnum)).get_value_as_int()
        shortname = 'readyslots_%d' % (slotnum)
        (labelwidget, label) = self.get_label_cache(shortname)
        (obj, origobj) = self.get_comp_objects()
        obj.readyslots[slotnum][0] = spell
        obj.readyslots[slotnum][1] = level
        self.set_changed_widget((origobj.readyslots[slotnum][0] == obj.readyslots[slotnum][0] and
            origobj.readyslots[slotnum][1] == obj.readyslots[slotnum][1]), shortname, labelwidget, label)

    def on_inv_clicked(self, widget, doshow=True):
        """ What to do when our inventory-item button is clicked. """
        wname = widget.get_name()
        (foo, row, col, bar) = wname.rsplit('_', 3)
        row = int(row)
        col = int(col)
        self.curitemtype = self.ITEM_INV
        self.curitem = (row, col)
        self.populate_itemform_from_item(self.char.inventory[row][col])
        self.get_widget('item_notebook').set_current_page(0)
        if (doshow):
            self.itemwindow.show()

    def on_equip_clicked(self, widget, doshow=True):
        """ What to do when our equipped-item button is clicked. """
        wname = widget.get_name()
        (equipname, foo) = wname.rsplit('_', 1)
        self.curitemtype = self.ITEM_EQUIP
        self.curitem = equipname
        self.populate_itemform_from_item(self.char.__dict__[equipname])
        self.get_widget('item_notebook').set_current_page(0)
        if (doshow):
            self.itemwindow.show()

    def on_ready_clicked(self, widget, doshow=True):
        """ What to do when our readied-item button is clicked. """
        wname = widget.get_name()
        (foo, num, bar) = wname.rsplit('_', 2)
        num = int(num)
        self.curitemtype = self.ITEM_READY
        self.curitem = num
        self.populate_itemform_from_item(self.char.readyitems[num])
        self.get_widget('item_notebook').set_current_page(0)
        if (doshow):
            self.itemwindow.show()

    def register_equip_change(self, name):
        """
        When loading in a new item, redraw the button and make sure that changes
        are entered into the system properly.
        """
        self.on_equip_clicked(self.get_widget('%s_button' % name), False)
        self.on_item_close_clicked(None, None, False)

    def register_inv_change(self, row, col):
        """
        When loading in a new item, redraw the button and make sure that changes
        are entered into the system properly.
        """
        self.on_inv_clicked(self.get_widget('inv_%d_%d_button' % (row, col)), False)
        self.on_item_close_clicked(None, None, False)

    def register_ready_change(self, num):
        """
        When loading in a new item, redraw the button and make sure that changes
        are entered into the system properly.
        """
        self.on_ready_clicked(self.get_widget('ready_%d_button' % (num)), False)
        self.on_item_close_clicked(None, None, False)

    def on_equip_action_clicked(self, widget):
        """ What to do when we cut/copy/paste/delete an equipped item. """
        wname = widget.get_name()
        (equipname, action) = wname.rsplit('_', 1)
        if (action == 'cut'):
            self.on_equip_action_clicked(self.get_widget('%s_copy' % equipname))
            self.on_equip_action_clicked(self.get_widget('%s_delete' % equipname))
        elif (action == 'copy'):
            self.itemclipboard = self.char.__dict__[equipname]
        elif (action == 'paste'):
            if (self.itemclipboard != None):
                self.char.__dict__[equipname] = self.itemclipboard.replicate()
                self.register_equip_change(equipname)
            pass
        elif (action == 'delete'):
            self.char.__dict__[equipname] = Item.new(c.book, True)
            self.register_equip_change(equipname)
        else:
            raise Exception('invalid action')

    def on_inv_action_clicked(self, widget):
        """ What to do when we cut/copy/paste/delete an inventory item. """
        wname = widget.get_name()
        (foo, row, col, action) = wname.rsplit('_', 3)
        row = int(row)
        col = int(col)
        if (action == 'cut'):
            self.on_inv_action_clicked(self.get_widget('inv_%d_%d_copy' % (row, col)))
            self.on_inv_action_clicked(self.get_widget('inv_%d_%d_delete' % (row, col)))
        elif (action == 'copy'):
            self.itemclipboard = self.char.inventory[row][col]
        elif (action == 'paste'):
            if (self.itemclipboard != None):
                self.char.inventory[row][col] = self.itemclipboard.replicate()
                self.register_inv_change(row, col)
        elif (action == 'delete'):
            self.char.inventory[row][col] = Item.new(c.book, True)
            self.register_inv_change(row, col)
        else:
            raise Exception('invalid action')

    def on_ready_action_clicked(self, widget):
        """ What to do when we cut/copy/paste/delete a readied item. """
        wname = widget.get_name()
        (foo, num, action) = wname.rsplit('_', 2)
        num = int(num)
        if (action == 'cut'):
            self.on_ready_action_clicked(self.get_widget('ready_%d_copy' % (num)))
            self.on_ready_action_clicked(self.get_widget('ready_%d_delete' % (num)))
        elif (action == 'copy'):
            self.itemclipboard = self.char.readyitems[num]
        elif (action == 'paste'):
            if (self.itemclipboard != None):
                self.char.readyitems[num] = self.itemclipboard.replicate()
                self.register_ready_change(num)
            pass
        elif (action == 'delete'):
            self.char.readyitems[num] = Item.new(c.book, True)
            self.register_ready_change(num)
        else:
            raise Exception('invalid action')

    def on_fxblock_button_clicked(self, widget):
        if self.char.book != 1:
            return
        fx0 = self.get_widget('fxblock_0')
        fx1 = self.get_widget('fxblock_1')
        fx2 = self.get_widget('fxblock_2')
        fx3 = self.get_widget('fxblock_3')
        idx = self.get_widget('fxblock_dropdown').get_active()
        if (idx == 1):
            fx0.set_value(1288490242)
            fx1.set_value(41023)
            fx2.set_value(38400)
            fx3.set_value(32000)
        elif (idx == 2):
            fx0.set_value(1803886340)
            fx1.set_value(61503)
            fx2.set_value(30720)
            fx3.set_value(15360)
        elif (idx == 3):
            fx0.set_value(1803886342)
            fx1.set_value(61503)
            fx2.set_value(38400)
            fx3.set_value(32000)
        else:
            fx0.set_value(1073741824)
            fx1.set_value(2111)
            fx2.set_value(2560)
            fx3.set_value(5120)

    def on_multarray_changed_fx(self, widget):
        self.on_multarray_changed(widget)
        if self.char.book != 1:
            return
        textwidget = self.get_widget('fxblock_text')
        fx0 = self.get_widget('fxblock_0').get_value_as_int()
        fx1 = self.get_widget('fxblock_1').get_value_as_int()
        fx2 = self.get_widget('fxblock_2').get_value_as_int()
        fx3 = self.get_widget('fxblock_3').get_value_as_int()
        fxstr = '(unknown)'
        if (fx0 == 1073741824 and
            fx1 == 2111 and
            fx2 == 2560 and
            fx3 == 5120):
            fxstr = 'None'
        elif (fx0 == 1803886340 and
            fx1 == 61503 and
            fx2 == 30720 and
            fx3 == 15360):
            fxstr = 'Gravedigger\'s Flame'
        elif (fx0 == 1288490242 and
            fx1 == 41023 and
            fx2 == 38400 and
            fx3 == 32000):
            fxstr = 'Torch'
        elif (fx0 == 1803886342 and
            fx1 == 61503 and
            fx2 == 38400 and
            fx3 == 32000):
            fxstr = 'Torch and Gravedigger\'s Flame'
        textwidget.set_markup('<span color="blue" style="italic">%s</span>' % (fxstr))

    def gtk_main_quit(self, widget=None, event=None):
        """ Main quit function. """
        if (self.has_unsaved_changes()):
            quitconfirm = self.get_widget('quitwindow')
            response = quitconfirm.run()
            quitconfirm.hide()
            if (response == gtk.RESPONSE_OK):
                gtk.main_quit()
            else:
                return True
        else:
            gtk.main_quit()

    def save_char(self, widget=None):
        """ Save character to disk. """
        self.char.write()
        self.clear_all_changes()
        self.putstatus('Saved ' + self.char.df.filename)
        self.origchar = self.char
        self.char = self.origchar.replicate()

    def populate_inv_button(self, row, col, orig=False):
        widget = self.get_widget('inv_%d_%d_text' % (row, col))
        imgwidget = self.get_widget('inv_%d_%d_image' % (row, col))
        if orig:
            item = self.origchar.inventory[row][col]
        else:
            item = self.char.inventory[row][col]
        self.populate_item_button(item, widget, imgwidget, self.get_widget('invtable%d' % (row)))

    def populate_equip_button(self, name, orig=False):
        widget = self.get_widget('%s_text' % (name))
        imgwidget = self.get_widget('%s_image' % (name))
        if orig:
            item = self.origchar.__dict__[name]
        else:
            item = self.char.__dict__[name]
        self.populate_item_button(item, widget, imgwidget, self.get_widget('equiptable'))

    def populate_ready_button(self, num, orig=False):
        widget = self.get_widget('ready_%d_text' % (num))
        imgwidget = self.get_widget('ready_%d_image' % (num))
        if orig:
            item = self.origchar.readyitems[num]
        else:
            item = self.char.readyitems[num]
        self.populate_item_button(item, widget, imgwidget, self.get_widget('readytable'))

    def on_revert(self, widget):
        """ What to do when we're told to Revert. """
        self.char = self.origchar.replicate()
        self.populate_form_from_char()
        self.clear_all_changes()

    def populate_form_from_char(self):
        """ Populates the GUI from our original char object. """
        char = self.origchar

        # Assign values
        self.get_widget('name').set_text(char.name)
        self.get_widget('level').set_value(char.level)
        if char.book == 1:
            self.get_widget('origin').set_text(char.origin)
            self.get_widget('axiom').set_text(char.axiom)
            self.get_widget('classname').set_text(char.classname)
            self.get_widget('picid').set_value(char.picid)
            self.on_singleval_changed_int_avatar(self.get_widget('picid'))
        else:
            self.get_widget('gender').set_active(char.gender-1)
            self.get_widget('b2origin').set_active(char.origin-1)
            self.get_widget('b2axiom').set_active(char.axiom-1)
            self.get_widget('b2classname').set_active(char.classname-1)
            if (char.picid < 13):
                self.get_widget('b2picid').set_active(char.picid-1)
            else:
                self.get_widget('b2picid').set_active(12)
            self.get_widget('hunger').set_value(char.hunger)
            self.get_widget('thirst').set_value(char.thirst)

        self.get_widget('strength').set_value(char.strength)
        self.get_widget('dexterity').set_value(char.dexterity)
        self.get_widget('endurance').set_value(char.endurance)
        self.get_widget('speed').set_value(char.speed)
        self.get_widget('intelligence').set_value(char.intelligence)
        self.get_widget('wisdom').set_value(char.wisdom)
        self.get_widget('perception').set_value(char.perception)
        self.get_widget('concentration').set_value(char.concentration)

        self.get_widget('curhp').set_value(char.curhp)
        self.get_widget('maxhp').set_value(char.maxhp)
        self.get_widget('curmana').set_value(char.curmana)
        self.get_widget('maxmana').set_value(char.maxmana)
        self.get_widget('experience').set_value(char.experience)
        self.get_widget('xpos').set_value(char.xpos)
        self.get_widget('ypos').set_value(char.ypos)
        self.get_widget('orientation').set_active(char.orientation-1)
        self.get_widget('extra_att_points').set_value(char.extra_att_points)
        self.get_widget('extra_skill_points').set_value(char.extra_skill_points)

        for num in range(1, len(c.skilltable)+1):
            self.get_widget('skills_%d' % (num)).set_value(char.skills[num])

        for num in range(len(c.statustable)):
            self.get_widget('statuses_%d' % (num)).set_value(char.statuses[num])
            if char.book == 2:
                self.get_widget('statuses_extra_%d' % (num)).set_value(char.statuses_extra[num])

        if char.book == 1:
            fxblocks = 4
        else:
            fxblocks = 7
        for num in range(fxblocks):
            self.get_widget('fxblock_%d' % (num)).set_value(char.fxblock[num])

        if char.book == 1:
            for key in c.diseasetable.keys():
                if (char.disease & key == key):
                    act = True
                else:
                    act = False
                widget = self.get_widget('disease_%04X' % (key))
                if widget:
                    widget.set_active(act)
        else:
            for key in c.permstatustable.keys():
                if (char.permstatuses & key == key):
                    act = True
                else:
                    act = False
                widget = self.get_widget('permstatuses_%08X' % (key))
                if widget:
                    widget.set_active(act)

        for i in range(len(c.spelltable)):
            self.get_widget('spells_%d' % (i)).set_active(char.spells[i])

        for i in range(10):
            self.get_widget('readyslots_spell_%d' % (i)).set_text(char.readyslots[i][0])
            self.get_widget('readyslots_level_%d' % (i)).set_value(char.readyslots[i][1])
        if char.book == 2:
            self.get_widget('readied_spell').set_text(char.readied_spell)
            self.get_widget('readied_spell_lvl').set_value(char.readied_spell_lvl)

        equiplist = [ 'helm', 'cloak', 'torso', 'gauntlet', 'belt', 'legs', 'feet',
                'amulet', 'ring1', 'ring2',
                'quiver', 'weap_prim', 'shield' ]
        if char.book == 1:
            equiplist.append('weap_alt')
        for equip in equiplist:
            self.populate_equip_button(equip, True)

        for row in range(char.inv_rows):
            for col in range(char.inv_cols):
                self.populate_inv_button(row, col, True)

        for num in range(char.ready_rows*char.ready_cols):
            self.populate_ready_button(num, True)

        self.get_widget('gold').set_value(char.gold)
        self.get_widget('torches').set_value(char.torches)
        self.get_widget('torchused').set_value(char.torchused)

        if char.book == 2:
            for num in range(6):
                self.get_widget('portal_loc_loc_%d' % (num)).set_value(char.portal_locs[num][0])
                self.get_widget('portal_loc_map_%d' % (num)).set_text(char.portal_locs[num][1])
                self.get_widget('portal_loc_mapeng_%d' % (num)).set_text(char.portal_locs[num][2])
            for idx in c.alchemytable.keys():
                self.get_widget('alchemy_book_%d' % (idx)).set_active(char.alchemy_book[idx] > 0)
            for (idx, key) in enumerate(char.keyring):
                self.get_widget('keyring_%d' % (idx)).set_text(key)

    def gui_finish(self):
        """
        Add in the rest of our GUI.  Right now this is all just Items, which each
        need to be basically identical blocks of related buttons, etc.  Glade just isn't
        good at dealing with arrays of widgets like that, so I'm doing it here instead of
        in there.  I don't like that we're breaking the whole display/application
        division, but this is far more maintainable in the long run.  I've honestly been
        considering folding in the rest of the forms into here as well, for similar reasons.
        gui_draw_int(), gui_draw_str(), etc.

        Note that this function will draw in the inventory size for Book 2 - the Book 1
        loading procedures should hide the extra data as-necessary.
        """

        # Update the title
        self.window.set_title('Eschalon Book %d Character Editor' % (c.book))

        # First our inventory
        inv_viewport = self.get_widget('inv_viewport')
        inv_book = gtk.Notebook()
        inv_book.show()
        inv_viewport.add(inv_book)
        self.register_widget('invnotebook', inv_book)
        for num in range(10):
            wind = gtk.ScrolledWindow()
            wind.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            wind.show()
            inv_book.append_page(wind, gtk.Label('Row %d' % (num+1)))
            vport = gtk.Viewport()
            vport.set_shadow_type(gtk.SHADOW_OUT)
            vport.show()
            wind.add(vport)
            self.gui_add_inv_page(vport, num)

        # Now our equipped items
        equip_viewport = self.get_widget('equip_viewport')
        self.gui_add_equip_page(equip_viewport)

        # Now our readied items
        ready_viewport = self.get_widget('ready_viewport')
        self.gui_add_ready_page(ready_viewport)

        #####
        ##### Now construct things that might be dependent on Book
        ##### (we were handling this in prepare_dynamic_form() on each
        ##### new character load until we split it out into its own
        ##### executable)
        #####

        # Make sure to handle the Item window too
        self.item_gui_finish(c.book)

        ###
        ### Front-screen skill table
        ###
        vbox = self.get_widget('charinfo_vbox')
        table = self.get_widget('skill_table')
        if table:
            vbox.remove(table)

        numrows = len(c.skilltable)/2
        if (len(c.skilltable) % 2 == 1):
            numrows += 1

        # Container Table
        table = gtk.Table(numrows, 5)
        self.register_widget('skill_table', table)
        spacelabel = gtk.Label('')
        spacelabel.set_size_request(20, -1)
        table.attach(spacelabel, 0, 1, 0, numrows, gtk.FILL, gtk.FILL)

        # Contents
        for (idx, skill) in enumerate(c.skilltable.values()):
            if (idx < numrows):
                row = idx
                col = 1
            else:
                row = idx-numrows
                col = 3
            label = gtk.Label('%s:' % (skill))
            label.set_alignment(1, .5)
            label.set_padding(4, 0)
            self.register_widget('skills_%d_label' % (idx+1), label)
            table.attach(label, col, col+1, row, row+1, gtk.FILL, gtk.FILL|gtk.EXPAND)
            
            align = gtk.Alignment(0.0, 0.5, 0.0, 1.0)
            table.attach(align, col+1, col+2, row, row+1, gtk.FILL, gtk.FILL|gtk.EXPAND)
            # TODO: limit is technically >255 on B1
            adjust = gtk.Adjustment(0, 0, 255, 1, 10, 0)
            spin = gtk.SpinButton(adjust)
            self.register_widget('skills_%d' % (idx+1), spin)
            align.add(spin)
            spin.connect('value-changed', self.on_multarray_changed)

        vbox.pack_start(table, False)
        table.show_all()

        ###
        ### Character Effects (non-permanent)
        ###
        cont = self.get_widget('status_alignment')
        table = self.get_widget('status_table')
        if table:
            cont.remove(table)

        numrows = len(c.statustable)/2
        if (len(c.statustable) % 2 == 1):
            numrows += 1

        # Container Table
        table = gtk.Table(numrows, 5)
        self.register_widget('status_table', table)
        spacelabel = gtk.Label('')
        spacelabel.set_size_request(20, -1)
        table.attach(spacelabel, 0, 1, 0, numrows, gtk.FILL, gtk.FILL)

        # Contents
        for (idx, skill) in enumerate(c.statustable.values()):
            if (idx < numrows):
                row = idx
                col = 1
            else:
                row = idx-numrows
                col = 3
            label = gtk.Label('%s:' % (skill))
            label.set_alignment(1, .5)
            label.set_padding(4, 0)
            self.register_widget('statuses_%d_label' % (idx), label)
            table.attach(label, col, col+1, row, row+1, gtk.FILL, gtk.FILL|gtk.EXPAND)
            
            align = gtk.Alignment(0.0, 0.5, 0.0, 1.0)
            table.attach(align, col+1, col+2, row, row+1, gtk.FILL, gtk.FILL|gtk.EXPAND)
            adjust = gtk.Adjustment(0, 0, 999, 1, 10, 0)
            spin = gtk.SpinButton(adjust)
            self.register_widget('statuses_%d' % (idx), spin)
            spin.connect('value-changed', self.on_effect_changed)
            if c.book == 1:
                align.add(spin)
            else:
                hbox = gtk.HBox()
                hbox.add(spin)
                adjust = gtk.Adjustment(0, 0, 999, 1, 10, 0)
                spin = gtk.SpinButton(adjust)
                self.register_widget('statuses_extra_%d' % (idx), spin)
                spin.connect('value-changed', self.on_effect_changed)
                hbox.add(spin)
                align.add(hbox)

        cont.add(table)
        table.show_all()

        ###
        ### Spell Checkboxes
        ###
        # TODO: should we alphabetize these?
        divbox = self.get_widget('divination_vbox')
        elembox = self.get_widget('elemental_vbox')
        for box in [divbox, elembox]:
            for child in box.get_children():
                box.remove(child)
        for (idx, spell) in c.spelltable.items():
            if c.spelltype[idx] == 'EL':
                box = elembox
            else:
                box = divbox
            cb = gtk.CheckButton()
            self.register_widget('spells_%d' % (idx), cb)
            label = gtk.Label(spell)
            self.register_widget('spells_%d_label' % (idx), label)
            cb.connect('toggled', self.on_checkbox_arr_changed)
            cb.add(label)
            box.pack_start(cb)
        elembox.show_all()
        divbox.show_all()

        ###
        ### Spell dropdowns
        ###
        # TODO: we should be able to do this all with a single listview, yeah?
        boxes = [self.get_widget('readied_spell_box')]
        for i in range(10):
            boxes.append(self.get_widget('readyslots_spell_%d_box' % (i)))
        spells = sorted(c.spelltable.values())
        for box in boxes:
            box.get_model().clear()
            box.append_text('')
            for spell in spells:
                box.append_text(spell)

        ###
        ### Alchemy Recipe Book
        ### Note that technically we don't need to do this dynamically, since
        ### these dropdowns only exist for Book 2.
        ###
        if c.book == 2:
            box1 = self.get_widget('alchemy_vbox_1')
            box2 = self.get_widget('alchemy_vbox_2')
            for box in [box1, box2]:
                for widget in box.get_children():
                    box.remove(widget)
            numrows = len(c.alchemytable)/2
            if (len(c.alchemytable) % 2 == 1):
                numrows += 1
            for (idx, recipe) in c.alchemytable.items():
                if (idx < numrows):
                    box = box1
                else:
                    box = box2
                cb = gtk.CheckButton()
                self.register_widget('alchemy_book_%d' % (idx), cb)
                label = gtk.Label(recipe)
                self.register_widget('alchemy_book_%d_label' % (idx), label)
                cb.connect('toggled', self.on_checkbox_arr_changed)
                cb.add(label)
                box.pack_start(cb)
            box1.show_all()
            box2.show_all()

        # Now show or hide form elements depending on the book version
        for char_class in (B1Character, B2Character, B1Item, B2Item):
            self.set_book_elem_visibility(char_class, char_class.book == c.book)

    def gui_item_page(self, container, pagetitle, rows, tablename):
        """ Sets up a page to store item information. """
        vbox = gtk.VBox()
        vbox.set_border_width(12)
        container.add(vbox)
        label = gtk.Label()
        label.set_markup(pagetitle)
        label.set_alignment(0, 0.5)
        label.set_padding(0, 5)
        label.expand = False
        vbox.pack_start(label, False)
        vbox.show()
        label.show()

        table = gtk.Table(rows, 3)
        table.show()
        self.register_widget(tablename, table)
        vbox.pack_start(table, False, True)
        spacelabel = gtk.Label('')
        spacelabel.show()
        spacelabel.set_size_request(20, -1)
        table.attach(spacelabel, 0, 1, 0, rows, gtk.FILL, gtk.FILL)
        return table

    def gui_add_equip_page(self, container):
        """ Create the equipped-item page. """
        table = self.gui_item_page(container, '<b>Equipped Items</b>', 14, 'equiptable')
        i = 0
        for item in [ ('helm', 'Helm'),
                ('cloak', 'Cloak'),
                ('torso', 'Torso'),
                ('gauntlet', 'Gauntlet'),
                ('belt', 'Belt'),
                ('legs', 'Legs'),
                ('feet', 'Feet'),
                ('amulet', 'Amulet'),
                ('ring1', 'Ring 1'),
                ('ring2', 'Ring 2'),
                ('quiver', 'Quiver'),
                ('weap_prim', 'Primary Weapon'),
                ('weap_alt', 'Alternate Weapon'),
                ('shield', 'Shield') ]:
            table.attach(self.gui_item_label('%s:' % item[1], '%s_label' % item[0]), 1, 2, i, i+1, gtk.FILL, gtk.FILL, 4)
            table.attach(self.gui_item(item[0], self.on_equip_clicked, self.on_equip_action_clicked),
                    2, 3, i, i+1, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 2)
            i = i + 1

    def gui_add_inv_page(self, container, rownum):
        """ Create an inventory page, given the row number. """
        if (rownum == 9):
            lines_to_alloc = 10
        else:
            lines_to_alloc = 8
        table = self.gui_item_page(container, '<b>Inventory Row %d</b>' % (rownum+1), lines_to_alloc, 'invtable%d' % (rownum))
        for num in range(8):
            table.attach(self.gui_item_label('Column %d:' % (num+1), 'inv_%d_%d_label' % (rownum, num)), 1, 2, num, num+1, gtk.FILL, gtk.FILL, 4)
            table.attach(self.gui_item('inv_%d_%d' % (rownum, num), self.on_inv_clicked, self.on_inv_action_clicked),
                    2, 3, num, num+1, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 2)
        if (rownum == 9):
            goldnote = gtk.Label()
            goldnote.set_alignment(0, 0.5)
            goldnote.set_markup('<i><b>Note:</b> Column seven is reserved in the GUI for displaying your gold count.  You should probably leave that slot empty.</i>')
            goldnote.set_line_wrap(True)
            goldnote.show()
            self.register_widget('b1_gold_note', goldnote)
            table.attach(goldnote, 2, 3, 8, 9, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 2)
            goldnote2 = gtk.Label()
            goldnote2.set_alignment(0, 0.5)
            goldnote2.set_markup('<i><b>Note:</b> Column eight is reserved in the GUI for displaying your gold count.  You should probably leave that slot empty.</i>')
            goldnote2.set_line_wrap(True)
            goldnote2.show()
            self.register_widget('b2_gold_note', goldnote2)
            table.attach(goldnote2, 2, 3, 9, 10, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 2)

    def gui_add_ready_page(self, container):
        """ Create a page for our readied items. """
        table = self.gui_item_page(container, '<b>Readied Items</b>', 10, 'readytable')
        for num in range(10):
            table.attach(self.gui_item_label('Item %d:' % (num+1), 'ready_%d_label' % (num)), 1, 2, num, num+1, gtk.FILL, gtk.FILL, 4)
            table.attach(self.gui_item('ready_%d' % (num), self.on_ready_clicked, self.on_ready_action_clicked),
                    2, 3, num, num+1, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 2)

    def open_avatarsel(self, widget):
        self.avatarsel.show()

    def avatarsel_on_motion(self, widget, event):
        self.avatarsel_mousex = int(event.x/self.avatarsel_width)
        if (self.avatarsel_mousex > self.avatarsel_cols):
            self.avatarsel_mousex = self.avatarsel_cols
        if (self.avatarsel_mousex != self.avatarsel_mousex_prev):
            self.avatarsel_clean.append(self.avatarsel_mousex_prev)
            self.avatarsel_clean.append(self.avatarsel_mousex)
            self.avatarsel_mousex_prev = self.avatarsel_mousex
        self.avatarsel_area.queue_draw()

    def avatarsel_draw(self, x):
        if (x < 0 or x >= self.avatarsel_cols or self.gfx is None):
            return
        pixbuf = self.gfx.get_avatar(x)
        if (pixbuf is None):
            return
        self.avatarsel_pixmap.draw_pixbuf(None, pixbuf, 0, 0, x*self.avatarsel_width, 0)
        if (x == self.avatarsel_mousex):
            color = self.gc_white
        elif (x == self.avatarsel_curx):
            color = self.gc_green
        else:
            return

        # Outline points
        x1 = x*self.avatarsel_width
        x2 = x1 + self.avatarsel_width - 1
        x3 = x2
        x4 = x1
        x5 = x1

        y1 = 0
        y2 = y1
        y3 = y2 + self.avatarsel_height - 1
        y4 = y3
        y5 = y1

        self.avatarsel_pixmap.draw_lines(color, [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5)])

    def avatarsel_on_expose(self, widget, event):
        if (self.avatarsel_init):
            for x in self.avatarsel_clean:
                self.avatarsel_draw(x)
        else:
            if (self.get_widget('picid').get_value_as_int() % 256 == 0):
                self.avatarsel_curx = self.get_widget('picid').get_value_as_int() / 256
            else:
                self.avatarsel_curx = -1
            self.avatarsel_area.set_size_request(self.avatarsel_x, self.avatarsel_y)
            self.avatarsel_pixmap = gtk.gdk.Pixmap(self.avatarsel_area.window, self.avatarsel_x, self.avatarsel_y)
            self.gc_white = gtk.gdk.GC(self.avatarsel_area.window)
            self.gc_white.set_rgb_fg_color(gtk.gdk.Color(65535, 65535, 65535))
            self.gc_black = gtk.gdk.GC(self.avatarsel_area.window)
            self.gc_black.set_rgb_fg_color(gtk.gdk.Color(0, 0, 0))
            self.gc_green = gtk.gdk.GC(self.avatarsel_area.window)
            self.gc_green.set_rgb_fg_color(gtk.gdk.Color(0, 65535, 0))
            self.avatarsel_pixmap.draw_rectangle(self.gc_black, True, 0, 0, self.avatarsel_x, self.avatarsel_y)
            for x in range(self.avatarsel_cols):
                self.avatarsel_draw(x)
            self.avatarsel_init = True
        self.avatarsel_clean = []
        self.avatarsel_area.window.draw_drawable(self.avatarsel_area.get_style().fg_gc[gtk.STATE_NORMAL],
            self.avatarsel_pixmap, 0, 0, 0, 0, self.avatarsel_x, self.avatarsel_y)

    def avatarsel_on_clicked(self, widget, event):
        self.avatarsel_init = False
        self.get_widget('picid').set_value(self.avatarsel_mousex * 256)
        self.avatarsel_mousex = -1
        self.avatarsel.hide()
