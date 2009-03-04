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
from eschalonb1 import flagstable

class BaseGUI:

    # Constants
    ITEM_NONE=0
    ITEM_EQUIP=1
    ITEM_INV=2
    ITEM_READY=3

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

    def item_init(self):
        """ Sets up some initial vars for handling items. """
        self.itemsel_init = False
        self.itemsel_clean = []
        self.itemsel_area = self.get_widget('itemsel_area')
        self.itemsel_x = 420
        self.itemsel_y = 1008
        self.itemsel_cols = 10
        self.itemsel_rows = 24
        self.itemsel_width = 42
        self.itemsel_height = 42
        self.itemsel_mousex = -1
        self.itemsel_mousey = -1
        self.itemsel_mousex_prev = -1
        self.itemsel_mousey_prev = -1

    def item_signals(self):
        """ Returns the signals that need to be attached for items. """
        return {
                'on_singleval_changed_str': self.on_singleval_changed_str,
                'on_singleval_changed_int': self.on_singleval_changed_int,
                'on_singleval_changed_int_itempic': self.on_singleval_changed_int_itempic,
                'on_dropdown_changed': self.on_dropdown_changed,
                'on_checkbox_changed': self.on_checkbox_changed,
                'on_checkbox_bit_changed': self.on_checkbox_bit_changed,
                'on_modifier_changed': self.on_modifier_changed,
                'on_item_close_clicked': self.on_item_close_clicked,
                'open_itemsel': self.open_itemsel,
                'itemsel_on_motion': self.itemsel_on_motion,
                'itemsel_on_expose': self.itemsel_on_expose,
                'itemsel_on_clicked': self.itemsel_on_clicked
                }

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

    def useful_combobox(self, box):
        ls = gtk.ListStore(gobject.TYPE_STRING)
        box.set_model(ls)
        cell = gtk.CellRendererText()
        box.pack_start(cell, True)
        box.add_attribute(cell, 'text', 0)

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
        else:
            obj = self.char
            origobj = self.origchar
        return (obj, origobj)

    def on_singleval_changed_str(self, widget):
        """ What to do when a string value changes. """
        wname = widget.get_name()
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_text()
        self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_singleval_changed_int(self, widget):
        """ What to do when an int value changes. """
        wname = widget.get_name()
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_value()
        # Note that for floats, we shouldn't do exact precision, hence the 1e-6 comparison here.
        self.set_changed_widget((abs(origobj.__dict__[wname] - obj.__dict__[wname])<1e-6), wname, labelwidget, label)

    def on_singleval_changed_int_itempic(self, widget):
        """ Special-case to handle changing the item picture properly. """
        self.on_singleval_changed_int(widget)
        self.get_widget('item_pic_image').set_from_pixbuf(self.gfx.get_item(widget.get_value()))
    
    def on_dropdown_changed(self, widget):
        """ What to do when a dropdown is changed """
        wname = widget.get_name()
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_active()
        self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_checkbox_changed(self, widget):
        """ What to do when a regular checkbox changes. """
        wname = widget.get_name()
        ischecked = widget.get_active()
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        if (ischecked):
            obj.__dict__[wname] = 1
        else:
            obj.__dict__[wname] = 0
        self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_checkbox_bit_changed(self, widget):
        """ What to do when a checkbox changes, and it's a bitfield. """
        wname = widget.get_name()
        ischecked = widget.get_active()
        (shortname, mask) = wname.rsplit('_', 1)
        mask = int(mask, 16)
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        if (ischecked):
            obj.__dict__[shortname] = obj.__dict__[shortname] | mask
        else:
            obj.__dict__[shortname] = obj.__dict__[shortname] & ~mask
        self.set_changed_widget((origobj.__dict__[shortname] & mask == obj.__dict__[shortname] & mask), wname, labelwidget, label)

    def on_modifier_changed(self, widget):
        """ What to do when our attr or skill modifier changes. """
        wname = widget.get_name()
        (which, type) = wname.rsplit('_', 1)
        modifiertext = '%s_modifier' % (which)
        modifiedtext = '%s_modified' % (which)
        modifier = self.get_widget(modifiertext).get_value()
        modified = self.get_widget(modifiedtext).get_active()
        (labelwidget, label) = self.get_label_cache(which)
        (obj, origobj) = self.get_comp_objects()
        if (wname == modifiertext):
            obj.__dict__[modifiertext] = modifier
        elif (wname == modifiedtext):
            obj.__dict__[modifiedtext] = modified
        self.set_changed_widget((origobj.__dict__[modifiertext] == obj.__dict__[modifiertext] and
            origobj.__dict__[modifiedtext] == obj.__dict__[modifiedtext]), which, labelwidget, label)

    def on_item_close_clicked(self, widget=None, dohide=True):
        if (self.curitemtype == self.ITEM_EQUIP):
            self.populate_equip_button(self.curitem)
        elif (self.curitemtype == self.ITEM_INV):
            self.populate_inv_button(self.curitem[0], self.curitem[1])
        elif (self.curitemtype == self.ITEM_READY):
            self.populate_ready_button(self.curitem)
        for name in self.itemchanged.keys():
            (labelwidget, label) = self.get_label_cache(name)
            self.set_changed_widget(True, name, labelwidget, label, False)
        self.itemchanged = {}
        self.curitemtype = self.ITEM_NONE
        if (dohide):
            self.itemwindow.hide()

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
        if (item.item_name == ''):
            imgwidget.set_from_stock(gtk.STOCK_EDIT, 4)
        else:
            imgwidget.set_from_pixbuf(self.gfx.get_item(item.pictureid, 26))
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

        for key in flagstable.keys():
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

        self.get_widget('visibility').set_value(item.visibility)
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
        strvals = [ 'item_name', 'script', 'emptystr' ]
        dropdownvals = [ 'type', 'subtype', 'incr' ]
        intvals = [ 'pictureid', 'value', 'weight', 'basedamage', 'basearmor',
                'hitpoint', 'mana', 'tohit', 'damage', 'armor',
                'visibility', 'duration', 'quantity', 'zero1' ]
        checkboxvals = [ 'canstack' ]
        checkboxbitvals = [ 'flags_0003' ]
        modifiervals = [ 'attr_modifier', 'skill_modifier' ]
        for val in strvals:
            self.on_singleval_changed_str(self.get_widget(val))
        for val in dropdownvals:
            self.on_dropdown_changed(self.get_widget(val))
        for val in intvals:
            self.on_singleval_changed_int(self.get_widget(val))
        for val in checkboxvals:
            self.on_checkbox_changed(self.get_widget(val))
        for val in checkboxbitvals:
            self.on_checkbox_bit_changed(self.get_widget(val))
        for val in modifiervals:
            self.on_modifier_changed(self.get_widget(val))

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
        tip = gtk.Tooltips()
        tip.set_tip(button, name)

        image = gtk.Image()
        image.show()
        image.set_from_stock(stockimage, 1)
        button.add(image)

        return button

    def open_itemsel(self, widget):
        self.itemsel.show()

    def itemsel_on_motion(self, widget, event):
        self.itemsel_mousex = int(event.x/self.itemsel_width)
        self.itemsel_mousey = int(event.y/self.itemsel_height)
        if (self.itemsel_mousex > self.itemsel_cols):
            self.itemsel_mousex = self.itemsel_cols
        if (self.itemsel_mousey > self.itemsel_rows):
            self.itemsel_mousey = self.itemsel_rows
        if (self.itemsel_mousex != self.itemsel_mousex_prev or
            self.itemsel_mousey != self.itemsel_mousey_prev):
            self.itemsel_clean.append((self.itemsel_mousex_prev, self.itemsel_mousey_prev))
            self.itemsel_clean.append((self.itemsel_mousex, self.itemsel_mousey))
            self.itemsel_mousex_prev = self.itemsel_mousex
            self.itemsel_mousey_prev = self.itemsel_mousey
        self.itemsel_area.queue_draw()

    def itemsel_draw(self, x, y):
        itemnum = (y*10)+x
        if (itemnum < 0 or itemnum > 239):
            return
        self.itemsel_pixmap.draw_pixbuf(None, self.gfx.get_item(itemnum), 0, 0, x*self.itemsel_width, y*self.itemsel_height)
        if (x == self.itemsel_mousex and y == self.itemsel_mousey):
            color = self.gc_white
        elif (x == self.itemsel_curx and y == self.itemsel_cury):
            color = self.gc_green
        else:
            return

        # Outline points
        x1 = x*self.itemsel_width
        x2 = x1 + self.itemsel_width - 1
        x3 = x2
        x4 = x1
        x5 = x1

        y1 = y*self.itemsel_height
        y2 = y1
        y3 = y2 + self.itemsel_height - 1
        y4 = y3
        y5 = y1

        self.itemsel_pixmap.draw_lines(color, [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5)])

    def itemsel_on_expose(self, widget, event):
        if (self.itemsel_init):
            for (x, y) in self.itemsel_clean:
                self.itemsel_draw(x, y)
        else:
            self.itemsel_curx = self.get_widget('pictureid').get_value() % 10
            self.itemsel_cury = int(self.get_widget('pictureid').get_value() / 10)
            self.itemsel_area.set_size_request(self.itemsel_x, self.itemsel_y)
            self.itemsel_pixmap = gtk.gdk.Pixmap(self.itemsel_area.window, self.itemsel_x, self.itemsel_y)
            self.gc_white = gtk.gdk.GC(self.itemsel_area.window)
            self.gc_white.set_rgb_fg_color(gtk.gdk.Color(65535, 65535, 65535))
            self.gc_black = gtk.gdk.GC(self.itemsel_area.window)
            self.gc_black.set_rgb_fg_color(gtk.gdk.Color(0, 0, 0))
            self.gc_green = gtk.gdk.GC(self.itemsel_area.window)
            self.gc_green.set_rgb_fg_color(gtk.gdk.Color(0, 65535, 0))
            self.itemsel_pixmap.draw_rectangle(self.gc_black, True, 0, 0, self.itemsel_x, self.itemsel_y)
            for y in range(self.itemsel_rows):
                for x in range(self.itemsel_cols):
                    self.itemsel_draw(x, y)
            self.itemsel_init = True
        self.itemsel_clean = []
        self.itemsel_area.window.draw_drawable(self.itemsel_area.get_style().fg_gc[gtk.STATE_NORMAL],
            self.itemsel_pixmap, 0, 0, 0, 0, self.itemsel_x, self.itemsel_y)

    def itemsel_on_clicked(self, widget, event):
        self.itemsel_init = False
        self.get_widget('pictureid').set_value(self.itemsel_mousex+(10*self.itemsel_mousey))
        self.itemsel.hide()
