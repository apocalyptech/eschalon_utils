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

import sys, os

# Load in our Glade stuff, required for now.
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

# Lookup tables we'll need
from EschalonB1 import Item, diseasetable, flagstable

# Constants
ITEM_NONE=0
ITEM_EQUIP=1
ITEM_INV=2
ITEM_READY=3

class MainGUI:

    def __init__(self, filename, char):

        self.filename = filename
        self.origchar = char
        self.char = char.replicate()
        self.labelcache = {}
        self.widgetcache = {}
        self.changed = {}

        # Support for our item screens
        self.curitemtype = ITEM_NONE
        self.curitem = ''
        self.itemchanged = {}
        self.itemclipboard = None

        # We need this because Not Everything's in Glade anymore
        # Note that we have a couple of widget caches now, so those should
        # be consolidated
        self.fullwidgetcache = {}

        # Start up our GUI
        self.gladefile = os.path.join(os.path.dirname(__file__), 'maingui.glade')
        self.wTree = gtk.glade.XML(self.gladefile)
        self.window = self.get_widget('mainwindow')
        self.itemwindow = self.get_widget('itemwindow')
        if (self.window):
            self.window.connect('destroy', gtk.main_quit)

        # GUI additions
        self.gui_finish()

        # Dictionary of signals.
        dic = { 'gtk_main_quit': self.gtk_main_quit,
                'on_revert': self.on_revert,
                'save_char': self.save_char,
                'on_fxblock_button_clicked': self.on_fxblock_button_clicked,
                'on_item_close_clicked': self.on_item_close_clicked,
                'on_checkbox_changed': self.on_checkbox_changed,
                'on_checkbox_bit_changed': self.on_checkbox_bit_changed,
                'on_checkbox_arr_changed': self.on_checkbox_arr_changed,
                'on_readyslots_changed': self.on_readyslots_changed,
                'on_multarray_changed': self.on_multarray_changed,
                'on_multarray_changed_fx': self.on_multarray_changed_fx,
                'on_singleval_changed_str': self.on_singleval_changed_str,
                'on_singleval_changed_int': self.on_singleval_changed_int,
                'on_modifier_changed': self.on_modifier_changed,
                'on_dropdown_changed': self.on_dropdown_changed,
                'on_dropdownplusone_changed': self.on_dropdownplusone_changed
                }
        self.wTree.signal_autoconnect(dic)

        # Populate the statusbar
        self.statusbar = self.get_widget('mainstatusbar')
        self.sbcontext = self.statusbar.get_context_id('Main Messages')
        self.putstatus('Editing ' + self.filename)

        # Load information from the character
        self.populate_form_from_char()

        # Load default dropdowns, since Glade apparently can't
        self.get_widget('fxblock_dropdown').set_active(0)

        # ... and start
        gtk.main()

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
        """ Returns a widget from our cache, or from wTree if it's not present in the cache. """
        if (not self.fullwidgetcache.has_key(name)):
            self.register_widget(name, self.wTree.get_widget(name), False)
        return self.fullwidgetcache[name]

    def check_item_changed(self):
        """
        Check to see if our item is changed, and if so, do the appropriate thing on the main form.
        """
        if self.curitemtype == ITEM_EQUIP:
            (labelwidget, label) = self.get_label_cache(self.curitem)
            labelname = labelwidget.get_name()
            (labelname, foo) = labelname.rsplit('_', 1)
            self.set_changed_widget((len(self.itemchanged) == 0), labelname, labelwidget, label, False)
        elif self.curitemtype == ITEM_INV:
            labelname = 'inv_%d_%d' % (self.curitem[0], self.curitem[1])
            (labelwidget, label) = self.get_label_cache(labelname)
            self.set_changed_widget((len(self.itemchanged) == 0), labelname, labelwidget, label, False)
        elif self.curitemtype == ITEM_READY:
            labelname = 'ready_%d' % (self.curitem)
            (labelwidget, label) = self.get_label_cache(labelname)
            self.set_changed_widget((len(self.itemchanged) == 0), labelname, labelwidget, label, False)
        else:
            pass

    def set_changed_widget(self, unchanged, name, labelwidget, label, doitem=True):
        """ Mark a label as changed or unchanged, on the GUI. """
        if (unchanged):
            if (not doitem or self.curitemtype == ITEM_NONE):
                if self.changed.has_key(name):
                    del self.changed[name]
            else:
                if self.itemchanged.has_key(name):
                    del self.itemchanged[name]
                self.check_item_changed()
            return labelwidget.set_markup(label)
        else:
            if (not doitem or self.curitemtype == ITEM_NONE):
                self.changed[name] = True
            else:
                self.itemchanged[name] = True
                self.check_item_changed()
            return labelwidget.set_markup('<span foreground="red">' + label + '</span>')

    def clear_all_changes(self):
        """ Clear out all the 'changed' notifiers on the GUI (used mostly just when saving). """
        # We'll have to make a copy of the dict on account of objectness
        mychanged = []
        for name in self.changed.keys():
            mychanged.append(name)
        for name in mychanged:
            (labelwidget, label) = self.get_label_cache(name)
            self.set_changed_widget(True, name, labelwidget, label)

    def get_comp_objects(self):
        """ Get the objects to compare against while checking for form changes. """
        if (self.curitemtype == ITEM_EQUIP):
            obj = self.char.__dict__[self.curitem]
            origobj = self.origchar.__dict__[self.curitem]
        elif (self.curitemtype == ITEM_INV):
            obj = self.char.inventory[self.curitem[0]][self.curitem[1]]
            origobj = self.origchar.inventory[self.curitem[0]][self.curitem[1]]
        elif (self.curitemtype == ITEM_READY):
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
    
    def on_dropdown_changed(self, widget):
        """ What to do when a dropdown is changed """
        wname = widget.get_name()
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_active()
        self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)
    
    def on_dropdownplusone_changed(self, widget):
        """ What to do when a dropdown is changed, when our index starts at 1. """
        wname = widget.get_name()
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[wname] = widget.get_active() + 1
        self.set_changed_widget((origobj.__dict__[wname] == obj.__dict__[wname]), wname, labelwidget, label)

    def on_multarray_changed(self, widget):
        """ What to do when an int value changes in an array. """
        wname = widget.get_name()
        (shortname, arrnum) = wname.rsplit('_', 1)
        arrnum = int(arrnum)
        (labelwidget, label) = self.get_label_cache(wname)
        (obj, origobj) = self.get_comp_objects()
        obj.__dict__[shortname][arrnum] = widget.get_value()
        self.set_changed_widget((origobj.__dict__[shortname][arrnum] == obj.__dict__[shortname][arrnum]), wname, labelwidget, label)

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

    def on_readyslots_changed(self, widget):
        """ What to do when one of our readied-spell slots changes. """
        wname = widget.get_name()
        (foo, slotnum) = wname.rsplit('_', 1)
        slotnum = int(slotnum)
        spell = self.get_widget('readyslots_spell_%d' % (slotnum)).get_text()
        level = self.get_widget('readyslots_level_%d' % (slotnum)).get_value()
        shortname = 'readyslots_%d' % (slotnum)
        (labelwidget, label) = self.get_label_cache(shortname)
        (obj, origobj) = self.get_comp_objects()
        obj.readyslots[slotnum][0] = spell
        obj.readyslots[slotnum][1] = level
        self.set_changed_widget((origobj.readyslots[slotnum][0] == obj.readyslots[slotnum][0] and
            origobj.readyslots[slotnum][1] == obj.readyslots[slotnum][1]), shortname, labelwidget, label)

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

    def on_inv_clicked(self, widget, doshow=True):
        """ What to do when our inventory-item button is clicked. """
        wname = widget.get_name()
        (foo, row, col, bar) = wname.rsplit('_', 3)
        row = int(row)
        col = int(col)
        self.curitemtype = ITEM_INV
        self.curitem = (row, col)
        self.populate_itemform_from_item(self.char.inventory[row][col])
        self.get_widget('item_notebook').set_current_page(0)
        if (doshow):
            self.itemwindow.show()

    def on_equip_clicked(self, widget, doshow=True):
        """ What to do when our equipped-item button is clicked. """
        wname = widget.get_name()
        (equipname, foo) = wname.rsplit('_', 1)
        self.curitemtype = ITEM_EQUIP
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
        self.curitemtype = ITEM_READY
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
        self.on_item_close_clicked(None, False)

    def register_inv_change(self, row, col):
        """
        When loading in a new item, redraw the button and make sure that changes
        are entered into the system properly.
        """
        self.on_inv_clicked(self.get_widget('inv_%d_%d_button' % (row, col)), False)
        self.on_item_close_clicked(None, False)

    def register_ready_change(self, num):
        """
        When loading in a new item, redraw the button and make sure that changes
        are entered into the system properly.
        """
        self.on_ready_clicked(self.get_widget('ready_%d_button' % (num)), False)
        self.on_item_close_clicked(None, False)

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
            self.char.__dict__[equipname] = Item.Item(True)
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
            pass
        elif (action == 'delete'):
            self.char.inventory[row][col] = Item.Item(True)
            self.register_inv_change(row, col)
        else:
            raise Exception('invalid action')

    def on_item_close_clicked(self, widget=None, dohide=True):
        if (self.curitemtype == ITEM_EQUIP):
            self.populate_equip_button(self.curitem)
        elif (self.curitemtype == ITEM_INV):
            self.populate_inv_button(self.curitem[0], self.curitem[1])
        elif (self.curitemtype == ITEM_READY):
            self.populate_ready_button(self.curitem)
        for name in self.itemchanged.keys():
            (labelwidget, label) = self.get_label_cache(name)
            self.set_changed_widget(True, name, labelwidget, label, False)
        self.itemchanged = {}
        self.curitemtype = ITEM_NONE
        if (dohide):
            self.itemwindow.hide()

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
            self.char.readyitems[num] = Item.Item(True)
            self.register_ready_change(num)
        else:
            raise Exception('invalid action')

    def on_fxblock_button_clicked(self, widget):
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
        textwidget = self.get_widget('fxblock_text')
        fx0 = self.get_widget('fxblock_0').get_value()
        fx1 = self.get_widget('fxblock_1').get_value()
        fx2 = self.get_widget('fxblock_2').get_value()
        fx3 = self.get_widget('fxblock_3').get_value()
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

    def gtk_main_quit(self, widget):
        """ Main quit function. """
        gtk.main_quit()

    def save_char(self, widget):
        """ Save character to disk. """
        self.char.write()
        self.clear_all_changes()
        self.putstatus('Saved ' + self.filename)
        self.origchar = self.char
        self.char = self.origchar.replicate()

    def populate_item_button(self, item, widget, tablewidget):
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
        # to resize buttons, we have to do this:
        tablewidget.check_resize()
        # ... that may be a gtk+ bug, have to submit that to find out.
        # http://bugzilla.gnome.org/show_bug.cgi?id=548094

    def populate_inv_button(self, row, col, orig=False):
        widget = self.get_widget('inv_%d_%d_text' % (row, col))
        if orig:
            item = self.origchar.inventory[row][col]
        else:
            item = self.char.inventory[row][col]
        self.populate_item_button(item, widget, self.get_widget('invtable%d' % (row)))

    def populate_equip_button(self, name, orig=False):
        widget = self.get_widget('%s_text' % (name))
        if orig:
            item = self.origchar.__dict__[name]
        else:
            item = self.char.__dict__[name]
        self.populate_item_button(item, widget, self.get_widget('equiptable'))

    def populate_ready_button(self, num, orig=False):
        widget = self.get_widget('ready_%d_text' % (num))
        if orig:
            item = self.origchar.readyitems[num]
        else:
            item = self.char.readyitems[num]
        self.populate_item_button(item, widget, self.get_widget('readytable'))

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
        self.get_widget('origin').set_text(char.origin)
        self.get_widget('axiom').set_text(char.axiom)
        self.get_widget('classname').set_text(char.classname)
        self.get_widget('level').set_value(char.level)
        self.get_widget('picid').set_value(char.picid)

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

        for num in range(1, 25):
            self.get_widget('skills_%d' % (num)).set_value(char.skills[num])

        for num in range(26):
            self.get_widget('statuses_%d' % (num)).set_value(char.statuses[num])

        for num in range(4):
            self.get_widget('fxblock_%d' % (num)).set_value(char.fxblock[num])

        for key in diseasetable.keys():
            if (char.disease & key == key):
                self.get_widget('disease_%04X' % (key)).set_active(True)

        for i in range(39):
            if (char.spells[i] > 0):
                self.get_widget('spells_%d' % (i)).set_active(True)

        for i in range(10):
            self.get_widget('readyslots_spell_%d' % (i)).set_text(char.readyslots[i][0])
            self.get_widget('readyslots_level_%d' % (i)).set_value(char.readyslots[i][1])

        for equip in [ 'helm', 'cloak', 'torso', 'gauntlet', 'belt', 'legs', 'feet',
                'amulet', 'ring1', 'ring2',
                'quiver', 'weap_prim', 'weap_alt', 'shield' ]:
            self.populate_equip_button(equip, True)

        for row in range(10):
            for col in range(7):
                self.populate_inv_button(row, col, True)

        for num in range(8):
            self.populate_ready_button(num, True)

        self.get_widget('gold').set_value(char.gold)
        self.get_widget('torches').set_value(char.torches)
        self.get_widget('torchused').set_value(char.torchused)

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

    def gui_finish(self):
        """
        Add in the rest of our GUI.  Right now this is all just Items, which each
        need to be basically identical blocks of related buttons, etc.  Glade just isn't
        good at dealing with arrays of widgets like that, so I'm doing it here instead of
        in there.  I don't like that we're breaking the whole display/application
        division, but this is far more maintainable in the long run.  I've honestly been
        considering folding in the rest of the forms into here as well, for similar reasons.
        gui_draw_int(), gui_draw_str(), etc.
        """

        # First our inventory
        inv_viewport = self.get_widget('inv_viewport')
        inv_book = gtk.Notebook()
        inv_book.show()
        inv_viewport.add(inv_book)
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
        table = self.gui_item_page(container, '<b>Inventory Row %d</b>' % (rownum+1), 7, 'invtable%d' % (rownum))
        for num in range(7):
            table.attach(self.gui_item_label('Column %d:' % (num+1), 'inv_%d_%d_label' % (rownum, num)), 1, 2, num, num+1, gtk.FILL, gtk.FILL, 4)
            table.attach(self.gui_item('inv_%d_%d' % (rownum, num), self.on_inv_clicked, self.on_inv_action_clicked),
                    2, 3, num, num+1, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 2)

    def gui_add_ready_page(self, container):
        """ Create a page for our readied items. """
        table = self.gui_item_page(container, '<b>Readied Items</b>', 8, 'readytable')
        for num in range(8):
            table.attach(self.gui_item_label('Item %d:' % (num+1), 'ready_%d_label' % (num)), 1, 2, num, num+1, gtk.FILL, gtk.FILL, 4)
            table.attach(self.gui_item('ready_%d' % (num), self.on_ready_clicked, self.on_ready_action_clicked),
                    2, 3, num, num+1, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 2)

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
        buttonimg.set_from_stock(gtk.STOCK_EDIT, 4)
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