#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Character Editor
# Copyright (C) 2008, 2009 CJ Kucera
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
import time
import cairo
import gobject
from eschalonb1.gfx import Gfx

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

from eschalonb1.map import Map
from eschalonb1.item import Item
from eschalonb1.square import Square
from eschalonb1.basegui import BaseGUI
from eschalonb1.mapscript import Mapscript
from eschalonb1.savefile import LoadException
from eschalonb1.entity import Entity
from eschalonb1 import app_name, version, url, authors, entitytable

class MapGUI(BaseGUI):

    def __init__(self, options, prefs):
        self.options = options
        self.prefs = prefs

    def run(self):

        # We need this because Not Everything's in Glade anymore
        # Note that we have a couple of widget caches now, so those should
        # be consolidated
        self.fullwidgetcache = {}

        # Let's make sure our map object exists
        self.map = None

        self.sq_x = -1
        self.sq_y = -1
        self.sq_x_prev = -1
        self.sq_y_prev = -1
        self.cleansquares = []

        self.mapinit = False

        # Start up our GUI
        self.gladefile = os.path.join(os.path.dirname(__file__), 'mapgui.glade')
        self.wTree = gtk.glade.XML(self.gladefile)
        self.itemfile = os.path.join(os.path.dirname(__file__), 'itemgui.glade')
        self.itemwTree = gtk.glade.XML(self.itemfile)
        self.window = self.get_widget('mainwindow')
        self.itemwindow = self.get_widget('itemwindow')
        self.squarewindow = self.get_widget('squarewindow')
        self.itemwindow.set_transient_for(self.squarewindow)
        self.propswindow = self.get_widget('globalpropswindow')
        self.drawstatuswindow = self.get_widget('drawstatus_window')
        self.drawstatusbar = self.get_widget('drawstatus_bar')
        self.maparea = self.get_widget('maparea')
        self.mapname_mainscreen_label = self.get_widget('mapname_mainscreen')
        self.coords_label = self.get_widget('coords')
        self.mainscroll = self.get_widget('mainscroll')
        self.zoom_in_button = self.get_widget('zoom_in_button')
        self.zoom_out_button = self.get_widget('zoom_out_button')
        self.floor_toggle = self.get_widget('floor_button')
        self.decal_toggle = self.get_widget('decal_button')
        self.object_toggle = self.get_widget('object_button')
        self.wall_toggle = self.get_widget('wall_button')
        self.tree_toggle = self.get_widget('tree_button')
        self.objectdecal_toggle = self.get_widget('objectdecal_button')
        self.entity_toggle = self.get_widget('entity_button')
        self.barrier_hi_toggle = self.get_widget('barrier_hi_button')
        self.script_hi_toggle = self.get_widget('script_hi_button')
        self.entity_hi_toggle = self.get_widget('entity_hi_button')
        self.script_notebook = self.get_widget('script_notebook')
        self.itemsel = self.get_widget('itemselwindow')
        self.floorsel = self.get_widget('floorselwindow')
        self.composite_area = self.get_widget('composite_area')
        if (self.window):
            self.window.connect('destroy', gtk.main_quit)

        # Initialize item stuff
        self.curitemtype = self.ITEM_MAP
        self.curitem = ''
        self.itemclipboard = None

        # Preferences window - also load in our graphics
        self.prefs_init(self.prefs)
        if (not self.require_gfx()):
            return
        self.gfx = Gfx(self.prefs)

        # Dictionary of signals.
        dic = { 'gtk_main_quit': self.gtk_main_quit,
                'on_load': self.on_load,
                'on_revert': self.on_revert,
                'on_about': self.on_about,
                'on_save': self.on_save,
                'on_save_as': self.on_save_as,
                'on_export_clicked': self.on_export_clicked,
                'on_clicked': self.on_clicked,
                'zoom_in': self.zoom_in,
                'zoom_out': self.zoom_out,
                'on_mouse_changed': self.on_mouse_changed,
                'expose_map': self.expose_map,
                'map_toggle': self.map_toggle,
                'on_healthmaxbutton_clicked': self.on_healthmaxbutton_clicked,
                'on_entid_changed': self.on_entid_changed,
                'on_singleval_square_changed_int': self.on_singleval_square_changed_int,
                'on_singleval_ent_changed_int': self.on_singleval_ent_changed_int,
                'on_singleval_ent_changed_str': self.on_singleval_ent_changed_str,
                'on_singleval_map_changed_int': self.on_singleval_map_changed_int,
                'on_singleval_map_changed_str': self.on_singleval_map_changed_str,
                'on_direction_changed': self.on_direction_changed,
                'on_entity_toggle': self.on_entity_toggle,
                'on_script_add': self.on_script_add,
                'on_floor_changed': self.on_floor_changed,
                'on_decal_changed': self.on_decal_changed,
                'on_wall_changed': self.on_wall_changed,
                'on_walldecal_changed': self.on_walldecal_changed,
                'on_colorsel_clicked': self.on_colorsel_clicked,
                'on_squarewindow_close': self.on_squarewindow_close,
                'on_prop_button_clicked': self.on_prop_button_clicked,
                'on_propswindow_close': self.on_propswindow_close,
                'on_prefs': self.on_prefs,
                'on_abort_render': self.on_abort_render,
                'open_floorsel': self.open_floorsel,
                'open_decalsel': self.open_decalsel,
                'open_walldecalsel': self.open_walldecalsel,
                'open_objsel': self.open_objsel,
                'objsel_on_motion': self.objsel_on_motion,
                'objsel_on_expose': self.objsel_on_expose,
                'objsel_on_clicked': self.objsel_on_clicked
                }
        dic.update(self.item_signals())
        # Really we should only attach the signals that will actually be sent, but this
        # should be fine here, anyway.
        self.wTree.signal_autoconnect(dic)
        self.itemwTree.signal_autoconnect(dic)

        # Manually connect a couple more signals that Glade can't handle for us automatically
        self.mainscroll.get_hadjustment().connect('changed', self.scroll_h_changed)
        self.mainscroll.get_vadjustment().connect('changed', self.scroll_v_changed)
        self.prev_scroll_h_cur = -1
        self.prev_scroll_h_max = -1
        self.prev_scroll_v_cur = -1
        self.prev_scroll_v_max = -1

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
        self.zoom_levels = [4, 8, 16, 24, 32, 52]
        self.set_zoom_vars(24)
        self.guicache = None
        self.squarebuf = None
        self.blanksquare = None
        self.basicsquare = None

        # Blank pixbuf to use in the square editing window
        self.comp_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 52, 130)

        # Load in our mouse map (to determine which square we're pointing at)
        self.mousemap = {}
        for zoom in self.zoom_levels:
            mapfile = os.path.join(os.path.dirname(__file__), 'iso_mousemap_%d.png' % (zoom))
            mapbuf = gtk.gdk.pixbuf_new_from_file(mapfile)
            try:
                self.mousemap[zoom] = mapbuf.get_pixels_array()
            except (RuntimeError, ImportError):
                self.mousemap[zoom] = self.stupid_pixels_array(mapbuf)

        # Process our entity list, for use in the entity type dropdown
        # This is.... Not the greatest.  Ah well.  Keeping the monsters
        # and NPCs sorted separately seems worth it
        monsters = {}
        npcs = {}
        for (key, item) in entitytable.iteritems():
            if (key < 51):
                table = monsters
            else:
                table = npcs
            table[item.name] = key
        monsterkeys = monsters.keys()
        monsterkeys.sort()
        npckeys = npcs.keys()
        npckeys.sort()
        self.entitykeys = monsterkeys
        self.entitykeys.extend(npckeys)
        self.entityrev = monsters
        self.entityrev.update(npcs)
        box = self.get_widget('entid')
        self.useful_combobox(box)
        for key in self.entitykeys:
            box.append_text(key)

        # Grab some lists of files
        maplist = self.get_gamedir_filelist('data', 'map', False)
        ogglist = self.get_gamedir_filelist('music', 'ogg')
        wavlist = self.get_gamedir_filelist('sound', 'wav', True, 'atmos_')

        # Populate the dropdowns on our global properties window
        self.populate_comboboxentry('exit_north_combo', maplist)
        self.populate_comboboxentry('exit_east_combo', maplist)
        self.populate_comboboxentry('exit_south_combo', maplist)
        self.populate_comboboxentry('exit_west_combo', maplist)
        self.populate_comboboxentry('soundfile1_combo', ogglist)
        self.populate_comboboxentry('soundfile2_combo', ogglist)
        self.populate_comboboxentry('soundfile3_combo', wavlist)
    
        # Now show our window
        self.window.show()

        # Now add an idle_timeout to initialize the map - this is how our
        # initial load happens
        gobject.idle_add(self.draw_map)

        # ... and get into the main gtk loop
        gtk.main()

    def putstatus(self, text):
        """ Pushes a message to the status bar """
        self.statusbar.push(self.sbcontext, text)

    def on_revert(self, widget):
        """ What to do when we're told to revert. """
        self.load_from_file(self.map.df.filename)

    def on_save(self, widget=None):
        """ Save map to disk. """
        self.map.write()
        self.putstatus('Saved ' + self.map.df.filename)

    def on_save_as(self, widget=None):
        """ Show the save-as dialog. """

        # Create the dialog
        dialog = gtk.FileChooserDialog('Save Map File...', None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE_AS, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.set_do_overwrite_confirmation(True)
        if (self.map != None):
            path = os.path.dirname(os.path.realpath(self.map.df.filename))
            if (path != ''):
                dialog.set_current_folder(path)

        filter = gtk.FileFilter()
        filter.set_name("Map Files")
        filter.add_pattern("*.map")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        # Run the dialog and process its return values
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.map.df.filename = dialog.get_filename()
            self.on_save()
            self.putstatus('Saved as %s' % (self.map.df.filename))
            self.get_widget('saveaswindow').run()
            self.get_widget('saveaswindow').hide()

        # Clean up
        dialog.destroy()

    def on_prefs(self, widget):
        """ Override on_prefs a bit. """
        (changed, alert_changed) = super(MapGUI, self).on_prefs(widget)
        if (changed and alert_changed):
            dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK)
            dialog.set_transient_for(self.window)
            dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            dialog.set_markup('<b>Note:</b> You must restart the application for the preferences change to take effect.')
            dialog.run()
            dialog.destroy()

    def on_export_clicked(self, widget=None):
        """ Used to export a PNG of the current map image to disk. """

        # Create the dialog
        dialog = gtk.FileChooserDialog('Export Image...', None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE_AS, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.set_do_overwrite_confirmation(True)
        infolabel = gtk.Label()
        infolabel.set_markup('<b>Note:</b> Only PNG images are supported.  If you name your export something other than .png, it will still be a PNG image.  Also note that an export at the fully-zoomed-in level will take about 25MB.')
        infolabel.set_line_wrap(True)
        dialog.set_extra_widget(infolabel)
        if (self.map != None):
            path = os.path.dirname(os.path.realpath(self.map.df.filename))
            if (path != ''):
                dialog.set_current_folder(path)

        filter = gtk.FileFilter()
        filter.set_name("PNG Files")
        filter.add_pattern("*.png")
        dialog.add_filter(filter)

        # Run the dialog and process its return values
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            self.guicache.write_to_png(filename)
            self.putstatus('Image exported to %s' % (filename))

        # Clean up
        dialog.destroy()

    # Use this to display the loading dialog, and deal with the main window accordingly
    def on_load(self, widget=None):
        
        # Blank out the main area
        #self.mainbook.set_sensitive(False)

        # Create the dialog
        dialog = gtk.FileChooserDialog('Open New Map File...', None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

        # Figure out what our initial path should be
        path = ''
        if (self.map == None):
            path = self.prefs.get_str('paths', 'savegames')
        else:
            path = os.path.dirname(os.path.realpath(self.map.df.filename))

        # Set the initial path
        if (path != '' and os.path.isdir(path)):
            dialog.set_current_folder(path)

        filter = gtk.FileFilter()
        filter.set_name("Map Files")
        filter.add_pattern("*.map")
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
            elif response == gtk.RESPONSE_CANCEL:
                # Check to see if this was the initial load, started without a filename
                if (self.map == None):
                    return False

        # Clean up
        dialog.destroy()
        #self.mainbook.set_sensitive(True)

        return True

    def register_widget(self, name, widget, doname=True):
        if doname:
            widget.set_name(name)
        self.fullwidgetcache[name] = widget

    def get_widget(self, name):
        """ Returns a widget from our cache, or from wTree if it's not present in the cache. """
        if (not self.fullwidgetcache.has_key(name)):
            if (self.wTree.get_widget(name) is None):
                self.register_widget(name, self.itemwTree.get_widget(name), False)
            else:
                self.register_widget(name, self.wTree.get_widget(name), False)
        return self.fullwidgetcache[name]

    # Use this to load in a map from a file
    def load_from_file(self, filename):

        # Load the file, if we can
        try:
            map = Map(filename)
            map.read()
        except LoadException, e:
            print e
            errordiag = self.get_widget('loaderrorwindow')
            errordiag.run()
            errordiag.hide()
            return False

        # Basic vars
        self.map = map

        # Update our status bar
        self.putstatus('Editing ' + self.map.df.filename)

        # Update the map title
        self.mapname_mainscreen_label.set_text(self.map.mapname)

        # Load information from the character
        if (self.mapinit):
            self.draw_map()

        # Return success
        return True

    def on_abort_render(self, widget=None):
        """
        A hard quit.  Not terribly friendly, but the way we're
        processing loading doesn't lend itself to graceful failbacks.
        This is mostly going to just be called if something goes
        catastrophically wrong, anyway.
        """
        sys.exit(0)

    def gtk_main_quit(self, widget=None, event=None):
        """ Main quit function. """
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL)
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.set_markup('Unsaved changes will be lost!  Continue?')
        response = dialog.run()
        dialog.destroy()
        if (response == gtk.RESPONSE_OK):
            gtk.main_quit()
        else:
            return True

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
            iconpath = os.path.join(os.path.dirname(__file__), 'eb1_icon_64.png')
            if (os.path.isfile(iconpath)):
                try:
                    about.set_logo(gtk.gdk.pixbuf_new_from_file(iconpath))
                except:
                    pass
            self.register_widget('aboutwindow', about, False)

        # Show the about dialog
        #self.mainbook.set_sensitive(False)
        about.run()
        about.hide()
        #self.mainbook.set_sensitive(True)

    def populate_color_selection(self):
        img = self.get_widget('color_img')
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 30, 30)
        pixbuf.fill(self.map.rgb_color())
        img.set_from_pixbuf(pixbuf)
        self.get_widget('color_rgb_label').set_markup('<i>(RGB: %d, %d, %d)</i>' %
                (self.map.color_r, self.map.color_g, self.map.color_b))

    def on_prop_button_clicked(self, widget):
        """ Show the global properties window. """
        self.get_widget('mapid').set_text(self.map.mapid)
        if (self.map.is_savegame()):
            self.get_widget('maptype').set_text('From Savegame')
        else:
            self.get_widget('maptype').set_text('Global Map File')
        self.get_widget('mapname').set_text(self.map.mapname)
        self.get_widget('exit_north').set_text(self.map.exit_north)
        self.get_widget('exit_east').set_text(self.map.exit_east)
        self.get_widget('exit_south').set_text(self.map.exit_south)
        self.get_widget('exit_west').set_text(self.map.exit_west)
        self.get_widget('soundfile1').set_text(self.map.soundfile1)
        self.get_widget('soundfile2').set_text(self.map.soundfile2)
        self.get_widget('soundfile3').set_text(self.map.soundfile3)
        self.get_widget('skybox').set_text(self.map.skybox)
        self.get_widget('parallax_1').set_value(self.map.parallax_1)
        self.get_widget('parallax_2').set_value(self.map.parallax_2)
        self.populate_color_selection()
        self.get_widget('color_a').set_value(self.map.color_a)
        self.get_widget('unknownh1').set_value(self.map.unknownh1)
        self.get_widget('unknowni1').set_value(self.map.unknowni1)
        self.get_widget('clouds').set_value(self.map.clouds)
        self.propswindow.show()

    def on_propswindow_close(self, widget, event=None):
        self.mapname_mainscreen_label.set_text(self.map.mapname)
        self.propswindow.hide()
        return True

    def on_colorsel_clicked(self, widget):
        dialog = gtk.ColorSelectionDialog('Select Overlay Color')
        dialog.set_transient_for(self.window)
        dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        dialog.colorsel.set_current_color(gtk.gdk.Color(self.map.color_r*257, self.map.color_g*257, self.map.color_b*257))
        response = dialog.run()
        if (response == gtk.RESPONSE_OK):
            color = dialog.colorsel.get_current_color()
            self.map.color_r = int(color.red/257)
            self.map.color_g = int(color.green/257)
            self.map.color_b = int(color.blue/257)
            self.populate_color_selection()
        dialog.destroy()

    def on_script_str_changed(self, widget):
        """ When a script string changes. """
        wname = widget.get_name()
        (labelname, page) = wname.rsplit('_', 1)
        page = int(page)
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        if (script is not None):
            if (labelname[:9] == 'item_name'):
                (varname, item_num) = labelname.rsplit('_', 1)
                item_num = int(item_num)
                script.items[item_num].item_name = widget.get_text()
            else:
                script.__dict__[labelname] = widget.get_text()

    def on_script_int_changed(self, widget):
        """ When a script integer changes. """
        wname = widget.get_name()
        (labelname, page) = wname.rsplit('_', 1)
        page = int(page)
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        if (script is not None):
            script.__dict__[labelname] = widget.get_value_as_int()

    def update_ent_square_img(self):
        entity = self.map.squares[self.sq_y][self.sq_x].entity
        entbuf = self.gfx.get_entity(entity.entid, entity.direction, None, True)
        if (entbuf is None):
            self.get_widget('ent_square_img').set_from_stock(gtk.STOCK_MISSING_IMAGE, 2)
        else:
            self.get_widget('ent_square_img').set_from_pixbuf(entbuf)

    def on_entid_changed(self, widget):
        """ Special case for changing the entity ID. """
        idx = widget.get_active()
        name = self.entitykeys[idx]
        entid = self.entityrev[name]
        self.map.squares[self.sq_y][self.sq_x].entity.entid = entid
        if (entid in entitytable):
            health = entitytable[entid].health
            button = self.get_widget('healthmaxbutton')
            button.set_label('Set to Max Health (%d)' % (health))
        self.update_ent_square_img()

    def on_direction_changed(self, widget):
        """ Special case for changing the entity direction. """
        wname = widget.get_name()
        ent = self.map.squares[self.sq_y][self.sq_x].entity
        ent.__dict__[wname] = widget.get_active() + 1
        self.update_ent_square_img()

    def on_singleval_ent_changed_int(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        ent = self.map.squares[self.sq_y][self.sq_x].entity
        ent.__dict__[wname] = widget.get_value_as_int()

    def on_singleval_ent_changed_str(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        ent = self.map.squares[self.sq_y][self.sq_x].entity
        ent.__dict__[wname] = widget.get_text()

    def on_singleval_map_changed_int(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        map = self.map
        map.__dict__[wname] = widget.get_value_as_int()

    def on_singleval_map_changed_str(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        map = self.map
        map.__dict__[wname] = widget.get_text()

    def on_singleval_square_changed_int(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        square = self.map.squares[self.sq_y][self.sq_x]
        square.__dict__[wname] = widget.get_value_as_int()

    def on_floor_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        pixbuf = self.gfx.get_floor(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('floorimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('floorimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_decal_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        pixbuf = self.gfx.get_decal(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('decalimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('decalimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_wall_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        (pixbuf, height) = self.gfx.get_object(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('wallimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('wallimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_walldecal_changed(self, widget):
        self.on_singleval_square_changed_int(widget)
        """ Update the appropriate image when necessary. """
        pixbuf = self.gfx.get_object_decal(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('walldecalimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('walldecalimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_squarewindow_close(self, widget, event=None):
        """
        Closes the square-editing window.  Our primary goal here is to redraw the
        square that was just edited.  Because we don't really keep composite caches
        around (should we?) this entails drawing all the squares behind the square we
        just edited, the square itself, and then four more "levels" of squares below, as
        well, because objects may be obscuring the one we just edited.  Because of the
        isometric presentation, this means that we'd be redrawing 29 total squares,
        assuming that everything fits exactly into our square width.

        Unfortunately, now that we support entities, some of those are wider than the
        square width, so we're going to redraw even more than that, for a total of 67
        squares.

        Note that we could cut down on that number by doing some logic - ie: we really
        would only have to draw the bottom-most square if it contained the tallest tree
        graphic, and there's no need to draw the floor or floor decals on any tile below
        the one we just edited.  Still, because this is a user-initiated action, I don't
        think it's really worth it to optimize that out.  I don't think the extra processing
        will be noticeable.

        Note that the we-don't-have-to-draw-everything angle becomes even bigger now that
        we're widening the field to support entities.  The outermost 20 squares that we're
        drawing only have to be drawn if there's an entity in there which is wider than
        the ordinary square, and even then we'd *only* have to draw the entity (to say nothing
        of the fact that very few of those larger entities actually draw to the full edge of
        the entity graphic for all cases).  Additionally, if the square we just edited didn't
        contain an entity at any point, we'd be able to lop off a bunch squares in the first
        place.  Still, I'm guessing that it doesn't really matter much.  Perhaps it'll become
        necessary to do this more intelligently once I've got some actual drawing-type
        functionality in place.

        Also note that absolutely none of this is necessary if the user didn't actually change
        anything.  Whatever.
        """

        # Figure out our dimensions
        tier_1_x = []
        tier_1_y = self.sq_y - 1 - 8
        tier_2_x = range(self.sq_x-1, self.sq_x+2)
        tier_2_y = self.sq_y - 8
        global_x = (self.sq_x * self.z_width) - self.z_halfwidth
        if ((self.sq_y % 2) == 0):
            tier_1_x = range(self.sq_x-2, self.sq_x+2)
        else:
            tier_1_x = range(self.sq_x-1, self.sq_x+3)
            global_x = global_x + self.z_halfwidth

        # Set up a surface to use
        over_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_width*2, self.z_5xheight)
        over_ctx = cairo.Context(over_surf)
        over_ctx.set_source_rgba(0, 0, 0, 1)
        over_ctx.paint()

        # Grab some local vars
        squares = self.map.squares

        # Loop through and composite the new image area
        for i in range(10):
            # Draw tier 1 squares first, then tier 2
            if (tier_1_y > -1 and tier_1_y < 200):
                for (tier_i, tier_x) in enumerate(tier_1_x):
                    yval = self.z_halfheight+((i-5)*self.z_height)
                    if (tier_x > -1 and tier_x < 100):
                        (op_buf, offset) = self.draw_square(tier_x, tier_1_y, False, False)
                        over_ctx.set_source_surface(op_buf, ((-3+(2*tier_i))*self.z_halfwidth)-offset+self.z_halfwidth, yval)
                        over_ctx.paint()
            if (i < 9):
                if (tier_2_y > -1 and tier_2_y < 200):
                    for (tier_i, tier_x) in enumerate(tier_2_x):
                        if (tier_x > -1 and tier_x < 100):
                            (op_buf, offset) = self.draw_square(tier_x, tier_2_y, False, False)
                            over_ctx.set_source_surface(op_buf, ((-1+tier_i)*self.z_width)-offset+self.z_halfwidth, (i-4)*self.z_height)
                            over_ctx.paint()
            tier_1_y = tier_1_y + 2
            tier_2_y = tier_2_y + 2

        # Now superimpose that onto our main map image
        self.guicache_ctx.set_source_surface(over_surf, global_x+1, self.z_halfheight*(self.sq_y-8)+1)
        self.guicache_ctx.paint()
        self.ctx.set_source_surface(over_surf, global_x+1, self.z_halfheight*(self.sq_y-8)+1)
        self.ctx.paint()
        self.cleansquares.append((self.sq_x, self.sq_y))
        self.maparea.queue_draw()

        # Finally, close out the window
        self.squarewindow.hide()
        return True

    def set_zoom_vars(self, width):
        """ Set a bunch of parameters we use to draw, based on how wide our squares should be. """
        self.curzoom = width
        self.z_width = width
        self.z_height = int(self.z_width/2)
        self.z_halfwidth = self.z_height
        self.z_halfheight = int(self.z_height/2)
        self.z_mapsize_x = self.z_width*101
        self.z_mapsize_y = int(self.z_mapsize_x/2)

        # These vars help speed up square drawing
        self.z_2xheight = self.z_height*2
        self.z_3xheight = self.z_height*3
        self.z_4xheight = self.z_height*4
        self.z_5xheight = self.z_height*5

    def scroll_h_changed(self, widget):
        """ Handle what to do when our scollwindow detects a change in dimensions. """
        if (self.prev_scroll_h_cur != -1):
            newval = int((self.prev_scroll_h_cur*widget.upper)/self.prev_scroll_h_max)
            # TODO: check for corner cases here, and in the v_changed as well
            if (widget.upper >= (newval + widget.page_size)):
                widget.set_value(newval)
        self.prev_scroll_h_max = widget.upper

    def scroll_v_changed(self, widget):
        """ Handle what to do when our scollwindow detects a change in dimensions. """
        if (self.prev_scroll_v_cur != -1):
            newval = int((self.prev_scroll_v_cur*widget.upper)/self.prev_scroll_v_max)
            if (widget.upper >= (newval + widget.page_size)):
                widget.set_value(newval)
        self.prev_scroll_v_max = widget.upper

    # Helper function for zooms, should rename this or something...
    def store_adjust(self):
        hadjust = self.mainscroll.get_hadjustment()
        vadjust = self.mainscroll.get_vadjustment()
        # TODO: This works for zooming-in, mostly...  Less good for zooming out.
        # I should figure out exactly what's going on.
        self.prev_scroll_h_cur = (hadjust.page_size/4)+hadjust.value
        self.prev_scroll_v_cur = (vadjust.page_size/4)+vadjust.value

    # TODO: Really need to normalize these...
    def zoom_out(self, widget):
        """ Handle a zoom-out. """
        curindex = self.zoom_levels.index(self.curzoom)
        if (curindex != 0):
            self.store_adjust()
            self.set_zoom_vars(self.zoom_levels[curindex-1])
            if (curindex == 1):
                self.zoom_out_button.set_sensitive(False)
            self.zoom_in_button.set_sensitive(True)
            self.draw_map()

    def zoom_in(self, widget):
        """ Handle a zoom-in. """
        curindex = self.zoom_levels.index(self.curzoom)
        if (curindex != (len(self.zoom_levels)-1)):
            self.store_adjust()
            self.set_zoom_vars(self.zoom_levels[curindex+1])
            if (curindex == (len(self.zoom_levels)-2)):
                self.zoom_in_button.set_sensitive(False)
            self.zoom_out_button.set_sensitive(True)
            self.draw_map()

    def on_mouse_changed(self, widget, event):
        """ Keep track of where the mouse is """

        # What x/y values we start with
        start_x = int(event.x/self.z_width)
        start_y = int(event.y/self.z_height)

        # Value to check inside our imagemap
        test_x = int(event.x - (start_x * self.z_width))
        test_y = int(event.y - (start_y * self.z_height))

        # We need to modify the y value before we actually process, though
        start_y = start_y * 2

        # ... and now figure out our coordinates based on the map
        # I tried out using a dict lookup instead of the series of if/then, but
        # the if/then ended up being about 40% faster or so.
        # TODO: Numeric fix here?  My upgrade to python 2.5 (numeric 24.2) necessitated the extra [0]
        testval = self.mousemap[self.curzoom][test_y][test_x][0][0]
        if (testval == 50):
            self.sq_x = start_x-1
            self.sq_y = start_y-1
        elif (testval == 100):
            self.sq_x = start_x
            self.sq_y = start_y-1
        elif (testval == 150):
            self.sq_x = start_x
            self.sq_y = start_y+1
        elif (testval == 200):
            self.sq_x = start_x-1
            self.sq_y = start_y+1
        else:
            self.sq_x = start_x
            self.sq_y = start_y

        # Some sanity checks
        if (self.sq_x < 0):
            self.sq_x = 0
        elif (self.sq_x > 99):
            self.sq_x = 99
        if (self.sq_y < 0):
            self.sq_y = 0
        elif (self.sq_y > 199):
            self.sq_y = 199

        # See if we've changed, and queue some redraws if so
        if (self.sq_x != self.sq_x_prev or self.sq_y != self.sq_y_prev):
            # It's possible we cause duplication here, but it the CPU cost should be negligible
            # It's also important to append the previous value FIRST, so that our graphic clean-up
            # doesn't clobber a freshly-drawn mouse pointer
            if (self.sq_x_prev != -1):
                self.cleansquares.append((self.sq_x_prev, self.sq_y_prev))
                # We should just really check for over-wide entities here, but for now we'll
                # just do some excessive redrawing.
                if (self.map.squares[self.sq_y_prev][self.sq_x_prev].entity is not None):
                    if (self.sq_x_prev != 0):
                        self.cleansquares.append((self.sq_x_prev-1, self.sq_y_prev))
                    if (self.sq_x_prev != 99):
                        self.cleansquares.append((self.sq_x_prev+1, self.sq_y_prev))
            self.cleansquares.append((self.sq_x, self.sq_y))
            self.sq_x_prev = self.sq_x
            self.sq_y_prev = self.sq_y
        self.coords_label.set_markup('<i>(%d, %d)</i>' % (self.sq_x, self.sq_y))

        # Now queue up a draw
        self.maparea.queue_draw()

    def set_entity_toggle_button(self, show_add):
        if (show_add):
            image = gtk.STOCK_ADD
            text = 'Add Entity'
            self.get_widget('entity_basic_box').hide()
            self.get_widget('entity_ext_box').hide()
        else:
            image = gtk.STOCK_REMOVE
            text = 'Remove Entity'
            self.get_widget('entity_basic_box').show()
            if (self.map.is_savegame()):
                self.get_widget('entity_ext_box').show()
            else:
                self.get_widget('entity_ext_box').hide()
        self.get_widget('entity_toggle_img').set_from_stock(image, 4)
        self.get_widget('entity_toggle_text').set_text(text)

    def input_label(self, page, table, row, name, text):
        label = gtk.Label()
        label.show()
        label.set_markup('%s:' % text)
        label.set_alignment(1, 0.5)
        label.set_padding(5, 4)
        label.set_name('%s_%d_label' % (name, page))
        table.attach(label, 1, 2, row, row+1, gtk.FILL, gtk.FILL)

    def input_text(self, page, table, row, name, text, tooltip=None):
        self.input_label(page, table, row, name, text)
        align = gtk.Alignment(0, 0.5, 0, 1)
        align.show()
        entry = gtk.Entry()
        entry.show()
        entry.set_name('%s_%d' % (name, page))
        entry.set_size_request(250, -1)
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        if (script is not None):
            if (name[:9] == 'item_name'):
                (varname, itemnum) = name.rsplit('_', 1)
                itemnum = int(itemnum)
                entry.set_text(script.items[itemnum].item_name)
            else:
                entry.set_text(script.__dict__[name])
        entry.connect('changed', self.on_script_str_changed)
        if (tooltip is not None):
            tips = gtk.Tooltips()
            tips.set_tip(entry, tooltip)
        align.add(entry)
        table.attach(align, 2, 3, row, row+1)

    def input_spin(self, page, table, row, name, text, max):
        self.input_label(page, table, row, name, text)
        align = gtk.Alignment(0, 0.5, 0, 1)
        align.show()
        entry = gtk.SpinButton()
        entry.show()
        entry.set_name('%s_%d' % (name, page))
        entry.set_range(0, max)
        entry.set_adjustment(gtk.Adjustment(0, 0, max, 1, 10, 10))
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        if (script is not None):
            entry.set_value(script.__dict__[name])
        entry.connect('value-changed', self.on_script_int_changed)
        align.add(entry)
        table.attach(align, 2, 3, row, row+1)

    def input_short(self, page, table, row, name, text):
        self.input_spin(page, table, row, name, text, 65535)

    def input_int(self, page, table, row, name, text):
        self.input_spin(page, table, row, name, text, 4294967295)

    def populate_mapitem_button(self, num, page):
        widget = self.get_widget('item_%d_%d_text' % (num, page))
        imgwidget = self.get_widget('item_%d_%d_image' % (num, page))
        item = self.map.squares[self.sq_y][self.sq_x].scripts[page].items[num]
        self.populate_item_button(item, widget, imgwidget, self.get_widget('itemtable_%d' % (page)))

    def on_mapitem_clicked(self, widget, doshow=True):
        """ What to do when our item button is clicked. """
        wname = widget.get_name()
        (varname, num, page, button) = wname.rsplit('_', 3)
        num = int(num)
        page = int(page)
        self.curitem = (num, page)
        self.populate_itemform_from_item(self.map.squares[self.sq_y][self.sq_x].scripts[page].items[num])
        self.get_widget('item_notebook').set_current_page(0)
        if (doshow):
            self.itemwindow.show()

    def register_mapitem_change(self, num, page):
        """
        When loading in a new item, redraw the button and make sure that changes
        are entered into the system properly.
        """
        self.on_mapitem_clicked(self.get_widget('item_%d_%d_button' % (num, page)), False)
        self.on_item_close_clicked(None, False)

    def on_mapitem_action_clicked(self, widget):
        """ What to do when we cut/copy/paste/delete an item. """
        wname = widget.get_name()
        (varname, num, page, action) = wname.rsplit('_', 3)
        num = int(num)
        page = int(page)
        items = self.map.squares[self.sq_y][self.sq_x].scripts[page].items
        if (action == 'cut'):
            self.on_mapitem_action_clicked(self.get_widget('item_%d_%d_copy' % (num, page)))
            self.on_mapitem_action_clicked(self.get_widget('item_%d_%d_delete' % (num, page)))
        elif (action == 'copy'):
            self.itemclipboard = items[num]
        elif (action == 'paste'):
            if (self.itemclipboard != None):
                items[num] = self.itemclipboard.replicate()
                self.register_mapitem_change(num, page)
        elif (action == 'delete'):
            items[num] = Item(True)
            items[num].tozero()
            self.register_mapitem_change(num, page)
        else:
            raise Exception('invalid action')

    def append_script_notebook(self, script):
        """
        Given a script, adds a new tab to the script notebook, with
        all the necessary inputs.
        """
        square = self.map.squares[self.sq_y][self.sq_x]
        curpages = self.script_notebook.get_n_pages()

        # Label for the notebook
        label = gtk.Label('Script #%d' % (curpages+1))
        label.show()

        # Remove Button
        remove_align = gtk.Alignment(0, 0.5, 0, 1)
        remove_align.show()
        remove_align.set_border_width(8)
        remove_button = gtk.Button()
        remove_button.show()
        remove_button.set_name('script_remove_button_%d' % (curpages))
        remove_button.connect('clicked', self.on_script_del)
        remove_button_box = gtk.HBox()
        remove_button_box.show()
        rm_img = gtk.image_new_from_stock(gtk.STOCK_REMOVE, 4)
        rm_img.show()
        remove_button_box.add(rm_img)
        rm_txt = gtk.Label('Remove Script')
        rm_txt.show()
        rm_txt.set_padding(6, 0)
        remove_button_box.add(rm_txt)
        remove_button.add(remove_button_box)
        remove_align.add(remove_button)

        # Basic Information
        basic_box = gtk.VBox()
        basic_box.show()
        basic_header = gtk.Label()
        basic_header.show()
        basic_header.set_markup('<b>Basic Information</b>')
        basic_header.set_alignment(0, 0.5)
        basic_header.set_padding(10, 7)
        basic_box.pack_start(basic_header, False, False)

        # Basic Table
        binput = gtk.Table(11, 3)
        binput.show()
        spacer = gtk.Label('')
        spacer.show()
        spacer.set_padding(11, 0)
        binput.attach(spacer, 0, 1, 0, 11, gtk.FILL, gtk.FILL|gtk.EXPAND)
        basic_box.pack_start(binput, False, False)

        # Basic Inputs
        self.input_text(curpages, binput, 0, 'description', 'Description / Map Link',
                'This is either a basic description of the square, or the name '
                'of a map, which will cause this square to act as a portal.')
        self.input_text(curpages, binput, 1, 'extratext', 'Extra Text / Map Coords',
                'More text (as from a sign or gravestone), or the destination '
                'coordinates within the map specified above, if this is a portal '
                'square.  The coordinate "(56, 129)" would be written "12956"')
        self.input_text(curpages, binput, 2, 'script', 'Script')
        self.input_short(curpages, binput, 3, 'flags', 'Flags <i>(probably)</i>')
        self.input_short(curpages, binput, 4, 'unknownh1', '<i>Unknown 1</i>')
        self.input_short(curpages, binput, 5, 'unknownh2', '<i>Unknown 2</i>')
        self.input_short(curpages, binput, 6, 'unknownh3', '<i>Unknown 3</i>')
        self.input_short(curpages, binput, 7, 'zeroh1', '<i>Usually Zero 1</i>')
        self.input_int(curpages, binput, 8, 'zeroi1', '<i>Usually Zero 2</i>')
        self.input_int(curpages, binput, 9, 'zeroi2', '<i>Usually Zero 3</i>')
        self.input_int(curpages, binput, 10, 'zeroi3', '<i>Usually Zero 4</i>')

        # Contents
        contents_box = gtk.VBox()
        contents_box.show()
        contents_header = gtk.Label()
        contents_header.show()
        contents_header.set_markup('<b>Contents</b> <i>(If Container)</i>')
        contents_header.set_alignment(0, 0.5)
        contents_header.set_padding(10, 7)
        contents_box.pack_start(contents_header, False, False)

        # Contents Table
        cinput = gtk.Table(8, 3)
        self.register_widget('itemtable_%d' % (curpages), cinput, True)
        cinput.show()
        cspacer = gtk.Label('')
        cspacer.show()
        cspacer.set_padding(11, 0)
        cinput.attach(cspacer, 0, 1, 0, 8, gtk.FILL, gtk.FILL|gtk.EXPAND)
        contents_box.pack_start(cinput, False, False)

        # Contents Inputs (varies based on savefile status)
        if (square.scripts[curpages].savegame):
            for num in range(8):
                self.input_label(curpages, cinput, num, 'item_%d_%d' % (num, curpages), 'Item %d' % (num+1))
                cinput.attach(self.gui_item('item_%d_%d' % (num, curpages), self.on_mapitem_clicked, self.on_mapitem_action_clicked),
                        2, 3, num, num+1, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND)
                self.populate_mapitem_button(num, curpages)
        else:
            for num in range(8):
                self.input_text(curpages, cinput, num, 'item_name_%d' % (num), 'Item %d' % (num+1))

        # Tab Content
        content = gtk.VBox()
        content.show()
        content.pack_start(remove_align, False, False)
        content.pack_start(basic_box, False, False)
        content.pack_start(contents_box, False, False)

        # ... aand we should slap this all into a scrolledwindow
        sw = gtk.ScrolledWindow()
        sw.show()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vp = gtk.Viewport()
        vp.show()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(content)
        sw.add(vp)

        self.script_notebook.append_page(sw, label)

    def clear_script_notebook(self):
        """ Clears out the script notebook. """
        for i in range(self.script_notebook.get_n_pages()):
            self.script_notebook.remove_page(0)

    def on_script_del(self, widget):
        """
        Called to remove a script.  This needs to handle renumbering the
        remaining scripts if necessary, too.
        """
        wname = widget.get_name()
        (button_name, page) = wname.rsplit('_', 1)
        page = int(page)
        square = self.map.squares[self.sq_y][self.sq_x]

        # We'll have to remove this regardless, so do it now.
        self.map.delscript(self.sq_x, self.sq_y, page)
        self.script_notebook.remove_page(page)

        # If we didn't just lop off the last one, redraw the whole notebook.
        # This is in theory more lame than renumbering stuff, but to accurately
        # renumber everything, we'd have to change the names of all the widgets
        # in there.  Which would be even more lame.
        if (page < len(square.scripts)):
            self.clear_script_notebook()
            for script in self.map.squares[self.sq_y][self.sq_x].scripts:
                self.append_script_notebook(script)

    def on_script_add(self, widget):
        """
        Called when a new script is added.  Creates a new
        Script object and handles adding it to the notebook.
        """
        square = self.map.squares[self.sq_y][self.sq_x]
        script = Mapscript(self.map.is_savegame())
        script.tozero(self.sq_x, self.sq_y)
        self.map.scripts.append(script)
        square.addscript(script)
        self.append_script_notebook(script)
        self.script_notebook.show()

    def on_healthmaxbutton_clicked(self, widget):
        """ Set the entity's health to its maximum. """
        entid = self.map.squares[self.sq_y][self.sq_x].entity.entid
        if (entid in entitytable):
            health = entitytable[entid].health
            self.get_widget('health').set_value(health)

    def on_entity_toggle(self, widget):
        square = self.map.squares[self.sq_y][self.sq_x]
        if (square.entity is None):
            # create a new entity and toggle
            ent = Entity(self.map.is_savegame())
            ent.tozero(self.sq_x, self.sq_y)
            self.map.entities.append(ent)
            square.addentity(ent)
            self.populate_entity_tab(square)
            self.set_entity_toggle_button(False)
        else:
            # Remove the existing entity
            self.map.delentity(self.sq_x, self.sq_y)
            self.set_entity_toggle_button(True)

    def populate_squarewindow_from_square(self, square):
        """ Populates the square editing screen from a given square. """

        # Make sure we start out on the right page
        self.get_widget('square_notebook').set_current_page(0)

        # First the main items
        self.get_widget('wall').set_value(square.wall)
        self.get_widget('floorimg').set_value(square.floorimg)
        self.get_widget('decalimg').set_value(square.decalimg)
        self.get_widget('wallimg').set_value(square.wallimg)
        self.get_widget('walldecalimg').set_value(square.walldecalimg)
        self.get_widget('scriptid').set_value(square.scriptid)
        self.get_widget('unknown5').set_value(square.unknown5)

        # Now entites, if needed
        if (square.entity is None):
            self.set_entity_toggle_button(True)
        else:
            self.set_entity_toggle_button(False)
            self.populate_entity_tab(square)

        # ... and scripts
        self.clear_script_notebook()
        if (len(square.scripts) > 0):
            for script in square.scripts:
                self.append_script_notebook(script)
            self.script_notebook.show()
        else:
            self.script_notebook.hide()

    def populate_entity_tab(self, square):
        """ Populates the entity tab of the square editing screen. """
        if (square.entity.entid in entitytable):
            if (entitytable[square.entity.entid].name in self.entitykeys):
                idx = self.entitykeys.index(entitytable[square.entity.entid].name)
                self.get_widget('entid').set_active(idx)
            else:
                # TODO: Warning/exit on here
                print "Not in keys"
                pass
        else:
            # TODO: Warning/exit on here
            print "Not in table"
            pass
        self.get_widget('direction').set_active(square.entity.direction-1)
        self.get_widget('script').set_text(square.entity.script)
        if (self.map.is_savegame()):
            self.get_widget('friendly').set_value(square.entity.friendly)
            self.get_widget('health').set_value(square.entity.health)
            self.get_widget('unknownc1').set_value(square.entity.unknownc1)
            self.get_widget('unknownc2').set_value(square.entity.unknownc2)
            self.get_widget('unknownc3').set_value(square.entity.unknownc3)
            self.get_widget('unknownc4').set_value(square.entity.unknownc4)
            self.get_widget('unknownc5').set_value(square.entity.unknownc5)
            self.get_widget('unknownc6').set_value(square.entity.unknownc6)

    def open_floorsel(self, widget):
        """ Show the floor selection window. """
        self.imgsel_launch(self.get_widget('floorimg'),
                52, 26, 6, 32,
                self.gfx.get_floor, True, 1)

    def open_decalsel(self, widget):
        """ Show the decal selection window. """
        self.imgsel_launch(self.get_widget('decalimg'),
                52, 26, 6, 32,
                self.gfx.get_decal, True, 1)

    def open_walldecalsel(self, widget):
        """ Show the wall decal selection window. """
        self.imgsel_launch(self.get_widget('walldecalimg'),
                52, 78, 6, 10,
                self.gfx.get_object_decal, True, 1)

    def objsel_fix_pixbuf(self, pixbuf):
        """ Function to fix the pixbuf, for object loading. """
        return pixbuf[0]

    def open_objsel(self, widget):
        """
        Launch our object selection window.  This is effectively
        an override of imgsel_launch() - we'll be playing some games
        to reduce code duplication here.  This should probably be
        in a class, somehow, instead of a dict.
        """
        self.imgsel_window = self.get_widget('objselwindow')
        self.imgsel_widget = self.get_widget('wallimg')
        self.objsel_book = self.get_widget('objsel_book')
        self.imgsel_bgcolor_img = self.get_widget('objsel_bgcolor_img')
        self.imgsel_bgcolor_event = self.get_widget('objsel_bgcolor_event')
        self.imgsel_getfunc = self.gfx.get_object
        self.imgsel_pixbuffunc = self.objsel_fix_pixbuf
        self.imgsel_init_bgcolor()
        self.imgsel_blank_color = self.imgsel_generate_grayscale(127)
        self.objsel_panes = {}
        self.objsel_panes['a'] = {
                'init': False,
                'clean': [],
                'area': self.get_widget('objsel_a_area'),
                'width': 52,
                'height': 52,
                'cols': 6,
                'rows': 16,
                'x': 52*6,
                'y': 52*16,
                'offset': 1,
                'mousex': -1,
                'mousey': -1,
                'mousex_prev': -1,
                'mousey_prev': -1,
                'blank': None,
            }
        self.objsel_panes['b'] = {
                'init': False,
                'clean': [],
                'area': self.get_widget('objsel_b_area'),
                'width': 52,
                'height': 78,
                'cols': 6,
                'rows': 10,
                'x': 52*6,
                'y': 78*10,
                'offset': 101,
                'mousex': -1,
                'mousey': -1,
                'mousex_prev': -1,
                'mousey_prev': -1,
                'blank': None,
            }
        self.objsel_panes['c'] = {
                'init': False,
                'clean': [],
                'area': self.get_widget('objsel_c_area'),
                'width': 52,
                'height': 78,
                'cols': 6,
                'rows': 10,
                'x': 52*6,
                'y': 78*10,
                'offset': 161,
                'mousex': -1,
                'mousey': -1,
                'mousex_prev': -1,
                'mousey_prev': -1,
                'blank': None,
            }
        self.objsel_panes['d'] = {
                'init': False,
                'clean': [],
                'area': self.get_widget('objsel_d_area'),
                'width': 52,
                'height': 130,
                'cols': 5,
                'rows': 1,
                'x': 52*5,
                'y': 130,
                'offset': 251,
                'mousex': -1,
                'mousey': -1,
                'mousex_prev': -1,
                'mousey_prev': -1,
                'blank': None,
            }
        # Set initial page
        curpage = 3
        letters = ['d', 'c', 'b', 'a']
        for letter in letters:
            if (self.imgsel_widget.get_value_as_int() >= self.objsel_panes[letter]['offset']):
                break
            curpage -= 1
        if (curpage < 0):
            curpage = 0
        self.objsel_book.set_current_page(curpage)
        self.objsel_current = ''
        #self.load_objsel_vars(self.get_widget('objsel_%s_area' % (letters[3-curpage])))
        self.imgsel_window.show()

    def load_objsel_vars(self, widget):
        """
        Given a widget (should be an object selection DrawingArea),
        populate the self.imgsel_* variables with the appropriate stuff.
        """
        wname = widget.get_name()
        (foo, letter, bar) = wname.split('_', 2)
        if (letter != self.objsel_current):
            for (key, val) in self.objsel_panes[letter].items():
                self.__dict__['imgsel_%s' % key] = val
            self.objsel_current = letter

    def objsel_on_clicked(self, widget, event):
        self.load_objsel_vars(widget)
        self.imgsel_on_clicked(widget, event)

    def objsel_on_expose(self, widget, event):
        self.load_objsel_vars(widget)
        self.imgsel_on_expose(widget, event)

    def objsel_on_motion(self, widget, event):
        self.load_objsel_vars(widget)
        self.imgsel_on_motion(widget, event)

    def on_clicked(self, widget, event):
        """ Handle a mouse click. """

        if (self.sq_y < len(self.map.squares)):
            if (self.sq_x < len(self.map.squares[self.sq_y])):
                self.populate_squarewindow_from_square(self.map.squares[self.sq_y][self.sq_x])
                self.get_widget('squarelabel').set_markup('<b>Map Square (%d, %d)</b>' % (self.sq_x, self.sq_y))
                self.squarewindow.show()

    def map_toggle(self, widget):
        self.draw_map()

    # Assumes that the context is squarebuf_ctx, hence the hardcoded width/height
    # We're passing it in so we're not constantly referencing self.squarebuf_ctx
    def composite_simple(self, context, surface, color):
        context.save()
        context.set_operator(cairo.OPERATOR_ATOP)
        context.set_source_rgba(*color)
        context.rectangle(0, 0, surface.get_width(), surface.get_height())
        context.fill()
        context.restore()

    def draw_square(self, x, y, usecache=False, do_main_paint=True):
        """ Draw a single square of the map. """

        # TODO: Layers are pretty inefficient and slow here, IMO
        barrier = False
        script = False
        pointer = False
        entity = False

        # Use local vars instead of continually calling out
        square = self.map.squares[y][x]
        sq_ctx = self.squarebuf_ctx
        main_ctx = self.ctx

        if (do_main_paint and x == self.sq_x and y == self.sq_y):
            pointer = (1, 1, 1, 0.5)

        if (square.entity is not None):
            entity = True
            if (square.entity.friendly == 1):
                entity = (0, 1, 0, 0.5)
            else:
                entity = (1, 0, 0, 0.5)

        if (square.scriptid != 0 and len(square.scripts) > 0):
            script = (1, 1, 0, 0.5)
        elif (square.scriptid != 0 and len(square.scripts) == 0):
            script = (0, .784, .784, 0.5)
        elif (square.scriptid == 0 and len(square.scripts) > 0):
            # afaik, this doesn't happen.  should use something other than red here, though
            script = (1, 0, 0, 0.5)

        if (square.wall == 1):
            barrier = (.784, .784, .784, 0.5)
        elif (square.wall == 5):
            barrier = (.684, .684, .950, 0.5)
        elif (square.floorimg == 126):
            barrier = (0, 0, .784, 0.5)

        # TODO: xpad processing should be abstracted somehow when we're drawing whole rows
        # (for instance, when initially loading the map)
        if (y % 2 == 1):
            xpad = self.z_halfwidth
        else:
            xpad = 0

        # Coordinates
        #      2
        #   1     3
        #      4
        xstart = (x*self.z_width)+xpad
        x1 = xstart+1
        x3 = xstart+self.z_width-1

        ystart = y*self.z_halfheight
        y2 = ystart+1
        y4 = ystart+self.z_height-1
        #if (y4-y2<3):
        #    # This is for our two most-zoomed-out levels
        #    y4 = y4 + 1
        #    y2 = y2 - 1

        # Area we're actually drawing
        top = y2-(self.z_4xheight)
        height = self.z_5xheight
        buftop = 0
        if (top<0):
            height = height+top
            buftop = -top
            top = 0

        # Simply redraw the area from our cache, if we should
        if (do_main_paint and usecache and not pointer):
            main_ctx.save()
            main_ctx.set_operator(cairo.OPERATOR_SOURCE)
            main_ctx.rectangle(x1, top, self.z_width, height)
            main_ctx.set_source_surface(self.guicache, 0, 0)
            main_ctx.fill()
            main_ctx.restore()
            return

        # Prepare our pixbuf
        sq_ctx.save()
        sq_ctx.set_operator(cairo.OPERATOR_SOURCE)
        if (do_main_paint and usecache):
            # If we're the pointer, always overlay our black square
            sq_ctx.set_source_surface(self.basicsquare)
        else:
            sq_ctx.set_source_surface(self.blanksquare)
        sq_ctx.paint()
        sq_ctx.restore()

        # Keep track of whether we've drawn anything or not
        drawn = False

        # Draw the floor tile
        if (self.floor_toggle.get_active()):
            pixbuf = self.gfx.get_floor(square.floorimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_4xheight)
                sq_ctx.paint()
                drawn = True

        # Draw the floor decal
        if (self.decal_toggle.get_active()):
            pixbuf = self.gfx.get_decal(square.decalimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_4xheight)
                sq_ctx.paint()
                drawn = True

        # Draw the object
        wallid = square.wallimg
        if (self.object_toggle.get_active() and wallid<161):
            (pixbuf, pixheight) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_height*(4-pixheight))
                sq_ctx.paint()
                drawn = True

        # Draw walls
        if (self.wall_toggle.get_active() and wallid<251 and wallid>160):
            (pixbuf, pixheight) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_height*(4-pixheight))
                sq_ctx.paint()
                drawn = True

        # Draw trees
        if (self.tree_toggle.get_active() and wallid>250):
            (pixbuf, pixheight) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_height*(4-pixheight))
                sq_ctx.paint()
                drawn = True

        # Draw the object decal
        if (self.objectdecal_toggle.get_active()):
            pixbuf = self.gfx.get_object_decal(square.walldecalimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_2xheight)
                sq_ctx.paint()
                drawn = True

        # Draw the entity if needed
        # We switch to using op_ctx and op_surf because we may not be drawing on sq_ctx
        # from this point on, depending on entity width
        op_surf = self.squarebuf
        op_ctx = sq_ctx
        op_xoffset = 0
        if (square.entity is not None and self.entity_toggle.get_active()):
            ent_img = self.gfx.get_entity(square.entity.entid, square.entity.direction, self.curzoom)
            if (ent_img is not None):
                if (ent_img.get_width() > self.curzoom):
                    self.ent_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, ent_img.get_width(), self.z_5xheight)
                    self.ent_ctx = cairo.Context(self.ent_surf)
                    op_xoffset = int((ent_img.get_width()-self.curzoom)/2)
                    self.ent_ctx.set_source_surface(op_surf, op_xoffset, 0)
                    self.ent_ctx.paint()
                    op_surf = self.ent_surf
                    op_ctx = self.ent_ctx
                op_ctx.set_source_surface(ent_img, 0, self.z_5xheight-ent_img.get_height())
                op_ctx.paint()
                drawn = True

        # Now, before we do highlights, see if we've drawn anything.  If not, 
        # overlay our basic black square, so that highlighting shows up if it
        # needs to.  If we *have* drawn something, just let it be.  (We do this
        # primarily to avoid graphical glitches on cliff-face graphics, where
        # having the black square overlay makes things look bad.)  Additionally
        # only do it if we would have done some highlighting.
        drawbarrier = (barrier and self.barrier_hi_toggle.get_active())
        drawscript = (script and self.script_hi_toggle.get_active())
        drawentity = (entity and self.entity_hi_toggle.get_active())
        if (not drawn and (drawbarrier or drawscript or drawentity)):
            sq_ctx.set_source_surface(self.basicsquare)
            sq_ctx.paint()

        # Draw Barrier Highlights
        # TODO: Drawing barriers on water is pretty lame; don't do that.
        # (perhaps unless asked to)
        if (drawbarrier):
            self.composite_simple(op_ctx, op_surf, barrier)

        # Draw Script Highlights
        if (drawscript):
            self.composite_simple(op_ctx, op_surf, script)

        # Draw Entity Highlights
        if (drawentity):
            self.composite_simple(op_ctx, op_surf, entity)

        # Now draw the pixbuf onto our pixmap
        if (do_main_paint):
            if (usecache):
                # We only get here when we're the pointer
                self.composite_simple(op_ctx, op_surf, pointer)
                main_ctx.set_source_surface(op_surf, x1-op_xoffset, top-buftop)
                main_ctx.paint()
            else:
                # This is only for the initial map population
                self.guicache_ctx.set_source_surface(op_surf, x1-op_xoffset, top-buftop)
                self.guicache_ctx.paint()

        return (op_surf, op_xoffset)

    def update_composite(self):

        # Grab our variables and clear out the pixbuf
        square = self.map.squares[self.sq_y][self.sq_x]
        comp_pixbuf = self.comp_pixbuf
        comp_pixbuf.fill(0)

        # Now do all the actual compositing
        if (square.floorimg > 0):
            pixbuf = self.gfx.get_floor(square.floorimg, 52, True)
            if (pixbuf is not None):
                pixbuf.composite(comp_pixbuf, 0, 104, 52, 26, 0, 104, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
        if (square.decalimg > 0):
            pixbuf = self.gfx.get_decal(square.decalimg, 52, True)
            if (pixbuf is not None):
                pixbuf.composite(comp_pixbuf, 0, 104, 52, 26, 0, 104, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
        if (square.wallimg > 0):
            (pixbuf, pixheight) = self.gfx.get_object(square.wallimg, 52, True)
            if (pixbuf is not None):
                pixbuf.composite(comp_pixbuf, 0, 26*(4-pixheight), 52, 26*(pixheight+1), 0, 26*(4-pixheight), 1, 1, gtk.gdk.INTERP_NEAREST, 255)
        if (square.walldecalimg > 0):
            pixbuf = self.gfx.get_object_decal(square.walldecalimg, 52, True)
            if (pixbuf is not None):
                pixbuf.composite(comp_pixbuf, 0, 52, 52, 78, 0, 52, 1, 1, gtk.gdk.INTERP_NEAREST, 255)

        # ... and update the main image
        self.get_widget('composite_area').set_from_pixbuf(comp_pixbuf)

    def draw_map(self):
        """
        This is the routine which sets up our initial map.  This used to be
        a part of expose_map, but this way we can throw up a progress dialog
        so the user's not wondering what's going on.

        Note that we're drawing to the main window HERE instead of in the
        setup areas of expose_map, so that the old map image stays onscreen
        for as long as possible.
        """

        # Timing, and statusbar
        time_a = time.time()
        self.drawstatusbar.set_fraction(0)
        self.drawstatuswindow.show()

        self.maparea.set_size_request(self.z_mapsize_x, self.z_mapsize_y)
        self.pixmap = gtk.gdk.Pixmap(self.maparea.window, self.z_mapsize_x, self.z_mapsize_y)

        self.ctx = self.pixmap.cairo_create()
        self.ctx.set_source_rgba(0, 0, 0, 1)
        self.ctx.paint()

        self.squarebuf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_width, self.z_5xheight)
        self.squarebuf_ctx = cairo.Context(self.squarebuf)
        self.guicache = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_mapsize_x, self.z_mapsize_y)
        self.guicache_ctx = cairo.Context(self.guicache)
        self.guicache_ctx.set_source_rgba(0, 0, 0, 1)
        self.guicache_ctx.paint()

        self.ent_surf = None
        self.ent_ctx = None

        # Set up a "blank" tile to draw everything else on top of
        self.blanksquare = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_width, self.z_5xheight)
        sq_ctx = cairo.Context(self.blanksquare)
        sq_ctx.save()
        sq_ctx.set_operator(cairo.OPERATOR_CLEAR)
        sq_ctx.paint()
        sq_ctx.restore()

        # Set up a default square with just a black tile, for otherwise-empty tiles
        self.basicsquare = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_width, self.z_5xheight)
        basic_ctx = cairo.Context(self.basicsquare)
        basic_ctx.set_source_rgba(0, 0, 0, 1)
        basic_ctx.move_to(0, self.z_4xheight+self.z_halfheight)
        basic_ctx.line_to(self.z_halfwidth, self.z_4xheight)
        basic_ctx.line_to(self.z_width, self.z_4xheight+self.z_halfheight)
        basic_ctx.line_to(self.z_halfwidth, self.z_5xheight)
        basic_ctx.close_path()
        basic_ctx.fill()

        # Draw the squares
        for y in range(len(self.map.squares)):
            for x in range(len(self.map.squares[y])):
                self.draw_square(x, y)
            self.drawstatusbar.set_fraction(y/float(len(self.map.squares)))
            while gtk.events_pending():
                gtk.main_iteration()

        # Finish drawing
        self.ctx.set_source_surface(self.guicache, 0, 0)
        self.ctx.paint()
        
        # ... and draw onto our main area (this is duplicated below, in expose_map)
        self.maparea.window.draw_drawable(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], self.pixmap, 0, 0, 0, 0, self.z_mapsize_x, self.z_mapsize_y)

        # Clean up our statusbar
        self.drawstatuswindow.hide()

        # Report timing
        time_b = time.time()
        print "Map rendered in %d seconds" % (int(time_b-time_a))

        # From now on, our map's considered initialized
        self.mapinit = True

        # Make sure we only do this once, when called from idle_add initially
        return False

    def expose_map(self, widget, event):

        # Don't bother to do anything unless we've been initialized
        if (self.mapinit):

            # Redraw what squares need to be redrawn
            for (x, y) in self.cleansquares:
                self.draw_square(x, y, True)

            # Render to the window (this is duplicated above, in draw_map)
            self.maparea.window.draw_drawable(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], self.pixmap, 0, 0, 0, 0, self.z_mapsize_x, self.z_mapsize_y)

            # Make sure our to-clean list is empty
            self.cleansquares = []
