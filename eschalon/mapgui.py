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
import csv
import sys
import time
import traceback
import cStringIO
from eschalon import constants as c
from eschalon.gfx import Gfx
from eschalon.undo import Undo
from eschalon.item import B1Item, B2Item
from eschalon.entity import B1Entity, B2Entity

# Load our GTK modules
try:
    import gtk
    import gobject
except Exception, e:
    print 'Python GTK Modules not found: %s' % (str(e))
    print 'Hit enter to exit...'
    sys.stdin.readline()
    sys.exit(1)

# Load in Cairo
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

from eschalon.map import Map
from eschalon.item import Item
from eschalon.square import Square
from eschalon.basegui import BaseGUI
from eschalon.smartdraw import SmartDraw
from eschalon.mapscript import Mapscript
from eschalon.savefile import LoadException
from eschalon.entity import Entity
from eschalon import app_name, version, url, authors

class MapGUI(BaseGUI):

    # Editing modes that we can be in
    MODE_EDIT = 0
    MODE_MOVE = 1
    MODE_DRAW = 2
    MODE_ERASE = 3

    # Actions that a mouse click can take
    ACTION_NONE = -1
    ACTION_EDIT = 0
    ACTION_DRAG = 1
    ACTION_DRAW = 2
    ACTION_ERASE = 4

    # Mouse button constants
    MOUSE_LEFT = 1
    MOUSE_MIDDLE = 2
    MOUSE_RIGHT = 3

    # Mouse Mappings for the various modes
    mouse_action_maps = {
        MODE_EDIT: {
            MOUSE_LEFT: ACTION_EDIT,
            MOUSE_MIDDLE: ACTION_DRAG,
            MOUSE_RIGHT: ACTION_DRAG
            },
        MODE_MOVE: {
            MOUSE_LEFT: ACTION_DRAG,
            MOUSE_MIDDLE: ACTION_DRAG,
            MOUSE_RIGHT: ACTION_EDIT
            },
        MODE_DRAW: {
            MOUSE_LEFT: ACTION_DRAW,
            MOUSE_MIDDLE: ACTION_DRAG,
            MOUSE_RIGHT: ACTION_EDIT
            },
        MODE_ERASE: {
            MOUSE_LEFT: ACTION_ERASE,
            MOUSE_MIDDLE: ACTION_DRAG,
            MOUSE_RIGHT: ACTION_EDIT
            }
        }

    def __init__(self, options, prefs, req_book):
        self.options = options
        self.prefs = prefs
        self.path_init()
        self.req_book = req_book
        c.switch_to_book(self.req_book)

        # Call out to the base initialization
        self.base_init()

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
        self.undo = None
        self.smartdraw = SmartDraw()

        # Start up our GUI
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.datafile('mapgui.ui'))
        self.builder.add_from_file(self.datafile('itemgui.ui'))
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
        self.zoom_scale = self.get_widget('zoom_scale')
        self.zoom_in_button = self.get_widget('zoom_in_button')
        self.zoom_out_button = self.get_widget('zoom_out_button')
        self.floor_toggle = self.get_widget('floor_button')
        self.decal_toggle = self.get_widget('decal_button')
        self.object_toggle = self.get_widget('object_button')
        self.wall_toggle = self.get_widget('wall_button')
        self.tree_toggle = self.get_widget('tree_button')
        self.objectdecal_toggle = self.get_widget('objectdecal_button')
        self.entity_toggle = self.get_widget('entity_button')
        self.huge_gfx_toggle = self.get_widget('huge_gfx_button')
        self.barrier_hi_toggle = self.get_widget('barrier_hi_button')
        self.script_hi_toggle = self.get_widget('script_hi_button')
        self.entity_hi_toggle = self.get_widget('entity_hi_button')
        self.script_notebook = self.get_widget('script_notebook')
        self.itemsel = self.get_widget('itemselwindow')
        self.floorsel = self.get_widget('floorselwindow')
        self.composite_area = self.get_widget('composite_area')
        self.ctl_edit_toggle = self.get_widget('ctl_edit_toggle')
        self.ctl_move_toggle = self.get_widget('ctl_move_toggle')
        self.ctl_draw_toggle = self.get_widget('ctl_draw_toggle')
        self.ctl_erase_toggle = self.get_widget('ctl_erase_toggle')
        self.menu_undo = self.get_widget('menu_undo')
        self.menu_undo_label = self.menu_undo.get_children()[0]
        self.menu_redo = self.get_widget('menu_redo')
        self.menu_redo_label = self.menu_redo.get_children()[0]
        self.draw_floor_checkbox = self.get_widget('draw_floor_checkbox')
        self.draw_floor_spin = self.get_widget('draw_floor_spin')
        self.draw_decal_checkbox = self.get_widget('draw_decal_checkbox')
        self.draw_decal_spin = self.get_widget('draw_decal_spin')
        self.draw_wall_checkbox = self.get_widget('draw_wall_checkbox')
        self.draw_wall_spin = self.get_widget('draw_wall_spin')
        self.draw_walldecal_checkbox = self.get_widget('draw_walldecal_checkbox')
        self.draw_walldecal_spin = self.get_widget('draw_walldecal_spin')
        self.draw_barrier = self.get_widget('draw_barrier')
        self.draw_barrier_seethrough = self.get_widget('draw_barrier_seethrough')
        self.erase_floor_checkbox = self.get_widget('erase_floor_checkbox')
        self.erase_decal_checkbox = self.get_widget('erase_decal_checkbox')
        self.erase_wall_checkbox = self.get_widget('erase_wall_checkbox')
        self.erase_walldecal_checkbox = self.get_widget('erase_walldecal_checkbox')
        self.erase_barrier = self.get_widget('erase_barrier')
        self.smartdraw_check = self.get_widget('smartdraw_check')
        self.smartdraw_container = self.get_widget('smartdraw_container')
        self.draw_smart_barrier = self.get_widget('draw_smart_barrier')
        self.draw_smart_wall = self.get_widget('draw_smart_wall')
        self.draw_smart_floor = self.get_widget('draw_smart_floor')
        self.smartdraw_floor_container = self.get_widget('smartdraw_floor_container')
        self.draw_straight_paths = self.get_widget('draw_straight_paths')
        self.draw_smart_walldecal = self.get_widget('draw_smart_walldecal')
        self.smart_randomize = self.get_widget('smart_randomize')
        self.smart_complex_objects = self.get_widget('smart_complex_objects')
        self.map_exception_window = self.get_widget('map_exception_window')
        self.map_exception_view = self.get_widget('map_exception_view')
        self.activity_label = self.get_widget('activity_label')
        self.draw_frame = self.get_widget('draw_frame')
        self.globalwarndialog = self.get_widget('globalwarndialog')
        self.globalwarn_check = self.get_widget('globalwarn_check')
        if (self.window):
            self.window.connect('destroy', gtk.main_quit)

        # The glade setting here doesn't seem to actually work
        self.ctl_edit_toggle.set_property('draw-indicator', False)
        self.ctl_move_toggle.set_property('draw-indicator', False)
        self.ctl_draw_toggle.set_property('draw-indicator', False)
        self.ctl_erase_toggle.set_property('draw-indicator', False)

        # Explicitly set our widget names (needed for gtk+ 2.20 compatibility)
        # See https://bugzilla.gnome.org/show_bug.cgi?id=591085
        for object in self.builder.get_objects():
            try:
                builder_name = gtk.Buildable.get_name(object)
                if builder_name:
                    object.set_name(builder_name)
            except TypeError:
                pass

        # Cursors for our editing modes
        self.edit_mode = self.MODE_EDIT
        self.cursor_move_drag = gtk.gdk.Cursor(gtk.gdk.DOT)
        self.cursor_map = {
            self.MODE_EDIT: None,
            self.MODE_MOVE: gtk.gdk.Cursor(gtk.gdk.FLEUR),
            self.MODE_DRAW: gtk.gdk.Cursor(gtk.gdk.PENCIL),
            self.MODE_ERASE: gtk.gdk.Cursor(gtk.gdk.CIRCLE)
            }

        # Initialize item stuff
        self.curitemtype = self.ITEM_MAP
        self.curitem = ''
        self.itemclipboard = None

        # Preferences window - also load in our graphics
        self.prefs_init(self.prefs)
        if (not self.require_gfx()):
            return
        self.gfx = Gfx.new(self.req_book, self.prefs, self.datadir)

        # Show a slow-loading zip warning if necessary
        if not self.gfx.fast_zipfile:
            self.get_widget('render_slowzip_warning').show()
            self.drawstatuswindow.set_size_request(350, 200)
            warn = self.prefs.get_bool('mapgui', 'warn_slow_zip')
            if warn:
                dialog = self.get_widget('slowzipwarndialog')
                resp = dialog.run()
                if(self.get_widget('slowzipwarn_check').get_active() != warn):
                    self.prefs.set_bool('mapgui', 'warn_slow_zip', self.get_widget('slowzipwarn_check').get_active())
                    self.prefs.save()
                dialog.hide()
                if resp != gtk.RESPONSE_OK:
                    sys.exit(1)

        # Now that we're sure we have a data dir, load in our entities
        self.populate_entities()

        # Register ComboBoxEntry child objects since the new Glade doesn't
        comboboxentries = ['exit_north', 'exit_east', 'exit_south', 'exit_west',
                'soundfile1', 'soundfile2', 'soundfile3', 'skybox']
        for var in comboboxentries:
            self.register_widget(var, self.get_widget('%s_combo' % (var)).child)
            self.get_widget(var).connect('changed', self.on_singleval_map_changed_str)

        # Finish populating Item windows (dependent on Book)
        self.window.set_title('Eschalon Book %d Map Editor' % (c.book))
        self.item_gui_finish(c.book)

        # Now show or hide form elements depending on the book version
        for item_class in (B1Item, B2Item, B1Entity, B2Entity):
            self.set_book_elem_visibility(item_class, item_class.book == c.book)

        # Dictionary of signals.
        dic = { 'gtk_main_quit': self.gtk_main_quit,
                'on_load': self.on_load,
                'on_revert': self.on_revert,
                'on_about': self.on_about,
                'on_save': self.on_save,
                'on_save_as': self.on_save_as,
                'on_export_clicked': self.on_export_clicked,
                'on_undo': self.on_undo,
                'on_redo': self.on_redo,
                'on_clicked': self.on_clicked,
                'on_released': self.on_released,
                'on_control_toggle': self.on_control_toggle,
                'key_handler': self.key_handler,
                'zoom_in': self.zoom_in,
                'zoom_out': self.zoom_out,
                'format_zoomlevel': self.format_zoomlevel,
                'on_mouse_changed': self.on_mouse_changed,
                'expose_map': self.expose_map,
                'map_toggle': self.map_toggle,
                'on_healthmaxbutton_clicked': self.on_healthmaxbutton_clicked,
                'on_setinitial_clicked': self.on_setinitial_clicked,
                'on_entid_changed': self.on_entid_changed,
                'on_scriptid_changed': self.on_scriptid_changed,
                'on_scriptid_dd_changed': self.on_scriptid_dd_changed,
                'on_singleval_square_changed_int': self.on_singleval_square_changed_int,
                'on_singleval_ent_changed_int': self.on_singleval_ent_changed_int,
                'on_singleval_ent_changed_str': self.on_singleval_ent_changed_str,
                'on_singleval_map_changed_int': self.on_singleval_map_changed_int,
                'on_singleval_map_changed_str': self.on_singleval_map_changed_str,
                'on_direction_changed': self.on_direction_changed,
                'on_map_flag_changed': self.on_map_flag_changed,
                'on_entity_toggle': self.on_entity_toggle,
                'on_script_add': self.on_script_add,
                'on_floor_changed': self.on_floor_changed,
                'on_draw_floor_changed': self.on_draw_floor_changed,
                'on_decal_changed': self.on_decal_changed,
                'on_draw_decal_changed': self.on_draw_decal_changed,
                'on_wall_changed': self.on_wall_changed,
                'on_draw_wall_changed': self.on_draw_wall_changed,
                'on_walldecal_changed': self.on_walldecal_changed,
                'on_draw_walldecal_changed': self.on_draw_walldecal_changed,
                'on_colorsel_clicked': self.on_colorsel_clicked,
                'on_squarewindow_close': self.on_squarewindow_close,
                'on_prop_button_clicked': self.on_prop_button_clicked,
                'on_propswindow_close': self.on_propswindow_close,
                'on_prefs': self.on_prefs,
                'on_abort_render': self.on_abort_render,
                'open_floorsel': self.open_floorsel,
                'open_draw_floorsel': self.open_draw_floorsel,
                'open_decalsel': self.open_decalsel,
                'open_draw_decalsel': self.open_draw_decalsel,
                'open_walldecalsel': self.open_walldecalsel,
                'open_draw_walldecalsel': self.open_draw_walldecalsel,
                'open_draw_objsel': self.open_draw_objsel,
                'open_objsel': self.open_objsel,
                'on_draw_smart_floor_toggled': self.on_draw_smart_floor_toggled,
                'objsel_on_motion': self.objsel_on_motion,
                'objsel_on_expose': self.objsel_on_expose,
                'objsel_on_clicked': self.objsel_on_clicked,
                'on_smartdraw_check_toggled': self.on_smartdraw_check_toggled,
                'draw_check_all': self.draw_check_all,
                'draw_uncheck_all': self.draw_uncheck_all,
                'highlight_check_all': self.highlight_check_all,
                'highlight_uncheck_all': self.highlight_uncheck_all,
                'update_activity_label': self.update_activity_label
                }
        dic.update(self.item_signals())
        # Really we should only attach the signals that will actually be sent, but this
        # should be fine here, anyway.
        self.builder.connect_signals(dic)

        # Event mask for processing hotkeys
        # (MOD2 is numlock; we don't care about that.  Dunno what 3-5 are, probably not used.)
        self.keymask = gtk.gdk.CONTROL_MASK|gtk.gdk.MOD1_MASK|gtk.gdk.MOD3_MASK
        self.keymask |= gtk.gdk.MOD4_MASK|gtk.gdk.MOD5_MASK

        # Manually connect a couple more signals that Glade can't handle for us automatically
        self.mainscroll.get_hadjustment().connect('changed', self.scroll_h_changed)
        self.mainscroll.get_vadjustment().connect('changed', self.scroll_v_changed)
        self.prev_scroll_h_cur = -1
        self.prev_scroll_h_max = -1
        self.prev_scroll_v_cur = -1
        self.prev_scroll_v_max = -1
        self.dragging = False
        self.drawing = False
        self.erasing = False

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

        # Set up our initial zoom levels and connect our signal to
        # the slider adjustment, so things work like we'd want.
        self.zoom_levels = [4, 8, 16, 24, 32, 52]
        if self.req_book == 2:
            self.zoom_levels.append(64)
        self.get_widget('map_zoom_adj').set_upper(len(self.zoom_levels)-1)
        default_zoom = self.prefs.get_int('mapgui', 'default_zoom')-1
        if (default_zoom >= len(self.zoom_levels)):
            default_zoom = len(self.zoom_levels)-1
        elif (default_zoom < 0):
            default_zoom = 0
        self.set_zoom_vars(default_zoom)
        self.zoom_adj = self.zoom_scale.get_adjustment()
        self.zoom_adj.set_value(default_zoom)
        self.zoom_adj.connect('value-changed', self.zoom_slider)

        # Some more vars to make sure exist
        self.guicache = None
        self.squarebuf = None
        self.blanksquare = None
        self.basicsquare = None
        self.updating_map_checkboxes = False

        # Blank pixbuf to use in the square editing window
        self.comp_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 52, 130)

        # Load in our mouse map (to determine which square we're pointing at)
        self.mousemap = {}
        for zoom in self.zoom_levels:
            mapfile = self.datafile('iso_mousemap_%d.png' % (zoom))
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
        for (key, item) in c.entitytable.iteritems():
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

        # And populate our object/script type dropdown as well
        self.object_type_list = {}
        self.object_type_list_rev = {}
        typebox = self.get_widget('scriptid_dd')
        self.useful_combobox(typebox)
        for (typeidx, (val, text)) in enumerate(c.objecttypetable.items()):
            typebox.append_text('%d - %s' % (val, text))
            self.object_type_list[val] = typeidx
            self.object_type_list_rev[typeidx] = val

        # ... initialize a couple of hidden spinboxes
        self.draw_floor_spin.set_value(1)
        self.draw_decal_spin.set_value(1)
        self.draw_wall_spin.set_value(1)
        self.draw_walldecal_spin.set_value(1)

        # Update our activity label
        self.update_activity_label()

        # Now show our window
        self.window.show()

        # Now add an idle_timeout to initialize the map - this is how our
        # initial load happens
        #gobject.idle_add(self.export_map_pngs)
        gobject.idle_add(self.draw_map)

        # ... and get into the main gtk loop
        gtk.main()

    def populate_entities(self):
        """
        Populates our entities, if need be.
        (Currently only does things for Book 2, since they can be sourced from
        a CSV file)
        """
        # x / y sizing
        # 0 / 0 1024x1024, sixteen to a row
        # 0 / 32 1024x1024, sixteen to a row
        # 32 / 0 1024x1024, ten to a row
        # 32 / 32 2048x2048, twenty-one to a row (with some left over)
        # 64 / 64 2048x2048, sixteen to a row
        if self.req_book != 2:
            return
        reader = csv.DictReader(cStringIO.StringIO(self.gfx.readfile('entities.csv', 'data')))
        for row in reader:
            xoff = int(row['Xoff'])
            yoff = int(row['Yoff'])
            width = 64 + xoff
            height = 64 + yoff
            c.entitytable[int(row['ID'])] = c.EntHelper(row['Name'],
                int(row['HP']),
                '%s.png' % (row['file']),
                int(row['Dirs']),
                int(row['Align']),
                width,
                height,
                int(row['Frame']))

    def putstatus(self, text):
        """ Pushes a message to the status bar """
        self.statusbar.push(self.sbcontext, text)

    def key_handler(self, widget, event):
        """ Handles keypresses, which we'll use to simplify selecting drawing stuff. """
        # TODO: check for Bad Things if we change while dragging, etc
        if (event.keyval < 256 and (event.state & self.keymask) == 0):
            key = chr(event.keyval).lower()
            if (key == 'm'):
                self.ctl_move_toggle.set_active(True)
            elif (key == 'e'):
                self.ctl_edit_toggle.set_active(True)
            elif (key == 'd'):
                self.ctl_draw_toggle.set_active(True)
            elif (key == 'r'):
                self.ctl_erase_toggle.set_active(True)

    def on_revert(self, widget=None):
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

    def on_prefs(self, widget=None):
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
            path = self.get_current_savegame_dir()
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
            else:
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
        """ Returns a widget from our cache, or from builder obj if it's not present in the cache. """
        if (not self.fullwidgetcache.has_key(name)):
            self.register_widget(name, self.builder.get_object(name), False)
        return self.fullwidgetcache[name]

    # Use this to load in a map from a file
    def load_from_file(self, filename):

        # Load the file, if we can
        try:
            map = Map.load(filename, None, self.req_book)
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

        # Instansiate our "undo" object so we can handle that
        self.undo = Undo(self.map)
        self.update_undo_gui()

        # Load the new map into our SmartDraw object
        self.smartdraw.set_map(self.map)
        self.smartdraw.set_gui(self)

        # Load information from the character
        if (self.mapinit):
            self.draw_map()

        # If we appear to be editing a global map file and haven't
        # been told otherwise, show a dialog warning the user
        warn = self.prefs.get_bool('mapgui', 'warn_global_map')
        if (not map.is_savegame() and warn and filename.find(self.get_current_gamedir()) != -1):
            self.globalwarn_check.set_active(warn)
            resp = self.globalwarndialog.run()
            self.globalwarndialog.hide()
            if (self.globalwarn_check.get_active() != warn):
                self.prefs.set_bool('mapgui', 'warn_global_map', self.globalwarn_check.get_active())
                self.prefs.save()

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
            iconpath = self.datafile('eb1_icon_64.png')
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

    def on_draw_smart_floor_toggled(self, widget):
        """ Handle the smart-floor toggling. """
        self.smartdraw_floor_container.set_sensitive(widget.get_active())

    def on_smartdraw_check_toggled(self, widget):
        """
        Deactivate/Activate smart draw functions
        """
        self.smartdraw_container.set_sensitive(widget.get_active())

    def update_undo_gui(self):
        """
        Handle updating things if undo or redo is called.  This
        will activate/deactivate the necessary menu items, etc.
        """
        if (self.undo.have_undo()):
            self.menu_undo.set_sensitive(True)
            history = self.undo.get_undo()
            self.menu_undo_label.set_text('Undo: %s to (%d, %d)' % (history.text, history.x, history.y))
        else:
            self.menu_undo.set_sensitive(False)
            self.menu_undo_label.set_text('Undo')
        if (self.undo.have_redo()):
            self.menu_redo.set_sensitive(True)
            history = self.undo.get_redo()
            self.menu_redo_label.set_text('Redo: %s to (%d, %d)' % (history.text, history.x, history.y))
        else:
            self.menu_redo.set_sensitive(False)
            self.menu_redo_label.set_text('Redo')
        #self.undo.report()

    def on_undo(self, widget=None):
        for (x, y) in self.undo.undo():
            self.redraw_square(x, y)
        self.update_undo_gui()

    def on_redo(self, widget=None):
        for (x, y) in self.undo.redo():
            self.redraw_square(x, y)
        self.update_undo_gui()

    def populate_color_selection(self):
        img = self.get_widget('color_img')
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 30, 30)
        pixbuf.fill(self.map.rgb_color())
        img.set_from_pixbuf(pixbuf)
        self.get_widget('color_rgb_label').set_markup('<i>(RGB: %d, %d, %d)</i>' %
                (self.map.color_r, self.map.color_g, self.map.color_b))

    def on_prop_button_clicked(self, widget=None):
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

    def on_locklevel_changed(self, widget):
        """ When our lock level changes. """
        self.on_script_int_changed(widget)
        wname = widget.get_name()
        (labelname, page) = wname.rsplit('_', 1)
        if c.book == 1:
            otherlabel = self.get_widget('other_%d_label' % (int(page)))
            if (widget.get_value_as_int() == 99):
                otherlabel.set_text('Slider Combination:')
            else:
                otherlabel.set_markup('<i>Other Value (0-3):</i>')
        else:
            sliderloot = self.get_widget('slider_loot_%d_label' % (int(page)))
            if (widget.get_value_as_int() == 12):
                sliderloot.set_text('Slider Combination:')
            else:
                sliderloot.set_markup('Loot Level (0-10):')

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
        if (entid in c.entitytable):
            health = c.entitytable[entid].health
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

    def on_draw_floor_changed(self, widget):
        """ Update the appropriate image when necessary. """
        pixbuf = self.gfx.get_floor(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('draw_floor_img').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('draw_floor_img').set_from_pixbuf(pixbuf)

    def on_decal_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        pixbuf = self.gfx.get_decal(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('decalimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('decalimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_draw_decal_changed(self, widget):
        """ Update the appropriate image when necessary. """
        pixbuf = self.gfx.get_decal(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('draw_decal_img').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('draw_decal_img').set_from_pixbuf(pixbuf)

    def on_wall_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        (pixbuf, height, offset) = self.gfx.get_object(widget.get_value_as_int(), None, True, self.map.tree_set)
        if (pixbuf is None):
            self.get_widget('wallimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('wallimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_draw_wall_changed(self, widget):
        """ Update the appropriate image when necessary. """
        (pixbuf, height, offset) = self.gfx.get_object(widget.get_value_as_int(), None, True, self.map.tree_set)
        if (pixbuf is None):
            self.get_widget('draw_wall_img').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('draw_wall_img').set_from_pixbuf(pixbuf)

    def on_walldecal_changed(self, widget):
        self.on_singleval_square_changed_int(widget)
        """ Update the appropriate image when necessary. """
        pixbuf = self.gfx.get_object_decal(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('walldecalimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('walldecalimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_draw_walldecal_changed(self, widget):
        """ Update the appropriate image when necessary. """
        pixbuf = self.gfx.get_object_decal(widget.get_value_as_int(), None, True)
        if (pixbuf is None):
            self.get_widget('draw_walldecal_img').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('draw_walldecal_img').set_from_pixbuf(pixbuf)

    def on_squarewindow_close(self, widget, event=None):
        """
        Closes the square-editing window.  Our primary goal here is to redraw the
        square that was just edited.  That's all out in its own function though, so
        we're just doing some housekeeping mostly.
        """
        # Populate our undo object with the new square
        # TODO: Note that we should really check for changes here so we're not storing empty
        # undo histories...
        self.undo.finish()

        # All the "fun" stuff ends up happening in here.
        self.redraw_square(self.sq_x, self.sq_y)
        
        # ... update our GUI stuff for Undo
        self.update_undo_gui()

        # Finally, close out the window
        self.squarewindow.hide()
        return True

    def redraw_square(self, x, y):
        """
        Redraw a single square, and any dependant squares nearby as well.

        Because we don't really keep composite caches
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
        tier_1_y = y - 1 - 8
        tier_2_x = range(x-1, x+2)
        tier_2_y = y - 8
        global_x = (x * self.z_width) - self.z_halfwidth
        if ((y % 2) == 0):
            tier_1_x = range(x-2, x+2)
        else:
            tier_1_x = range(x-1, x+3)
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
        self.guicache_ctx.set_source_surface(over_surf, global_x+1, self.z_halfheight*(y-8)+1)
        self.guicache_ctx.paint()
        self.ctx.set_source_surface(over_surf, global_x+1, self.z_halfheight*(y-8)+1)
        self.ctx.paint()
        self.cleansquares.append((x, y))
        self.maparea.queue_draw()

        return True

    def format_zoomlevel(self, widget, value):
        """ Formats the zoom slider scale. """
        return 'Lvl %d' % (value+1)

    def set_zoom_vars(self, scalenum):
        """
        Set a bunch of parameters we use to draw, based on how wide our squares should be.
        This also incidentally sets the sensitivity flag on our zoom buttons.
        """
        width = self.zoom_levels[scalenum]
        self.curzoomidx = scalenum
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

        # Our squarebuf size (the one we draw squares onto) may vary based on book
        self.z_squarebuf_w = int(self.z_width * self.gfx.squarebuf_mult)
        self.z_squarebuf_offset = int((self.z_squarebuf_w - self.z_width)/2)

        # Clean up our zoom icons
        if (scalenum == 0):
            self.zoom_out_button.set_sensitive(False)
        else:
            self.zoom_out_button.set_sensitive(True)
        if (scalenum == len(self.zoom_levels)-1):
            self.zoom_in_button.set_sensitive(False)
        else:
            self.zoom_in_button.set_sensitive(True)

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

    def zoom_to(self, level):
        """ Take care of everything that needs to be done when we change zoom levels. """
        hadjust = self.mainscroll.get_hadjustment()
        vadjust = self.mainscroll.get_vadjustment()
        # TODO: This works for zooming-in, mostly...  Less good for zooming out.
        # I should figure out exactly what's going on.
        self.prev_scroll_h_cur = (hadjust.page_size/4)+hadjust.value
        self.prev_scroll_v_cur = (vadjust.page_size/4)+vadjust.value
        self.set_zoom_vars(level)
        self.draw_map()

    def zoom_slider(self, widget):
        """ Handle a zoom from the slider. """
        newzoom = int(widget.get_value())
        if (newzoom < 0):
            newzoom = 0
        if (newzoom > len(self.zoom_levels)-1):
            newzoom = len(self.zoom_levels)-1
        if (newzoom != self.curzoomidx):
            self.zoom_to(newzoom)

    def zoom_out(self, widget):
        """ Handle a zoom-out. """
        if (self.curzoomidx != 0):
            self.zoom_scale.set_value(self.curzoomidx-1)

    def zoom_in(self, widget):
        """ Handle a zoom-in. """
        if (self.curzoomidx != (len(self.zoom_levels)-1)):
            self.zoom_scale.set_value(self.curzoomidx+1)

    def on_mouse_changed(self, widget, event):
        """ Keep track of where the mouse is """

        if (self.dragging):
            diff_x = self.hold_x - event.x_root
            diff_y = self.hold_y - event.y_root
            if (diff_x != 0):
                adjust = self.mainscroll.get_hadjustment()
                newvalue = adjust.get_value() + diff_x
                if (newvalue < adjust.lower):
                    newvalue = adjust.lower
                elif (newvalue > adjust.upper-adjust.page_size):
                    newvalue = adjust.upper-adjust.page_size
                adjust.set_value(newvalue)
            if (diff_y != 0):
                adjust = self.mainscroll.get_vadjustment()
                newvalue = adjust.get_value() + diff_y
                if (newvalue < adjust.lower):
                    newvalue = adjust.lower
                elif (newvalue > adjust.upper-adjust.page_size):
                    newvalue = adjust.upper-adjust.page_size
                adjust.set_value(newvalue)
            self.hold_x = event.x_root
            self.hold_y = event.y_root
            return

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
        testval = self.mousemap[self.curzoom][test_y][test_x][0]
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

            # Draw if we're supposed to
            if (self.drawing):
                self.action_draw_square(self.sq_x, self.sq_y)
            elif (self.erasing):
                self.action_erase_square(self.sq_x, self.sq_y)

        self.coords_label.set_markup('<i>(%d, %d)</i>' % (self.sq_x, self.sq_y))

        # Now queue up a draw
        self.maparea.queue_draw()

    def set_entity_toggle_button(self, show_add):
        if (show_add):
            image = gtk.STOCK_ADD
            text = 'Add Entity'
            self.get_widget('entity_basic_box').hide()
            self.get_widget('entity_extra_box').hide()
        else:
            image = gtk.STOCK_REMOVE
            text = 'Remove Entity'
            self.get_widget('entity_basic_box').show()
            if (self.map.is_savegame()):
                self.get_widget('entity_extra_box').show()
            else:
                self.get_widget('entity_extra_box').hide()
        self.get_widget('entity_toggle_img').set_from_stock(image, 4)
        self.get_widget('entity_toggle_text').set_text(text)

    def input_label(self, page, table, row, name, text):
        label = gtk.Label()
        label.show()
        label.set_markup('%s:' % text)
        label.set_alignment(1, 0.5)
        label.set_justify(gtk.JUSTIFY_RIGHT)
        label.set_padding(5, 4)
        self.register_widget('%s_%d_label' % (name, page), label)
        table.attach(label, 1, 2, row, row+1, gtk.FILL, gtk.FILL)

    def input_text(self, page, table, row, name, text, tooltip=None):
        self.input_label(page, table, row, name, text)
        align = gtk.Alignment(0, 0.5, 0, 1)
        align.show()
        entry = gtk.Entry()
        entry.show()
        self.register_widget('%s_%d' % (name, page), entry)
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
            entry.set_tooltip_text(tooltip)
        align.add(entry)
        table.attach(align, 2, 3, row, row+1)

    def input_spin(self, page, table, row, name, text, max, tooltip=None, signal=None):
        self.input_label(page, table, row, name, text)
        align = gtk.Alignment(0, 0.5, 0, 1)
        align.show()
        entry = gtk.SpinButton()
        entry.show()
        self.register_widget('%s_%d' % (name, page), entry)
        entry.set_range(0, max)
        entry.set_adjustment(gtk.Adjustment(0, 0, max, 1, 10, 0))
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        if (script is not None):
            entry.set_value(script.__dict__[name])
        if (signal is None):
            entry.connect('value-changed', self.on_script_int_changed)
        else:
            entry.connect('value-changed', signal)
        if (tooltip is not None):
            entry.set_tooltip_text(tooltip)
        align.add(entry)
        table.attach(align, 2, 3, row, row+1)

    def input_uchar(self, page, table, row, name, text, tooltip=None, signal=None):
        self.input_spin(page, table, row, name, text, 0xFF, tooltip, signal)

    def input_short(self, page, table, row, name, text, tooltip=None):
        self.input_spin(page, table, row, name, text, 0xFFFF, tooltip)

    def input_int(self, page, table, row, name, text, tooltip=None):
        self.input_spin(page, table, row, name, text, 0xFFFFFFFF, tooltip)

    def input_dropdown(self, page, table, row, name, text, values, tooltip=None, signal=None):
        self.input_label(page, table, row, name, text)
        align = gtk.Alignment(0, 0.5, 0, 1)
        align.show()
        entry = gtk.combo_box_new_text()
        entry.show()
        entry.set_name('%s_%d' % (name, page))
        for value in values:
            entry.append_text(value)
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        if (script is not None):
            entry.set_active(script.__dict__[name])
        if (signal is not None):
            entry.connect('changed', signal)
        else:
            entry.connect('changed', self.on_dropdown_changed)
        if (tooltip is not None):
            entry.set_tooltip_text(tooltip)
        align.add(entry)
        table.attach(align, 2, 3, row, row+1)

    def input_flag(self, page, table, row, name, flagval, text, tooltip=None):
        self.input_label(page, table, row, name, text)
        align = gtk.Alignment(0, 0.5, 0, 1)
        align.show()
        entry = gtk.CheckButton()
        entry.show()
        entry.set_name('%s_%X_%d' % (name, flagval, page))
        scriptval = self.map.squares[self.sq_y][self.sq_x].scripts[page].__dict__[name]
        entry.set_active((scriptval & flagval == flagval))
        entry.connect('toggled', self.on_script_flag_changed)
        if (tooltip is not None):
            entry.set_tooltip_text(tooltip)
        align.add(entry)
        table.attach(align, 2, 3, row, row+1)

    def on_flag_changed(self, name, flagval_str, widget, object):
        """
        What to do whan a bit field changes.  Currently just the
        destructible flag.
        """
        flagval = int(flagval_str, 16)
        if (object is not None):
            if (widget.get_active()):
                object.__dict__[name] = object.__dict__[name] | flagval
            else:
                object.__dict__[name] = object.__dict__[name] & ~flagval

    def on_map_flag_changed(self, widget):
        """
        What to do whan a bit field changes.  Currently just the
        destructible flag.
        """
        wname = widget.get_name()
        (name, flagval) = wname.rsplit('_', 1)
        square = self.map.squares[self.sq_y][self.sq_x]
        self.on_flag_changed(name, flagval, widget, square)

    def on_script_flag_changed(self, widget):
        """
        What to do whan a bit field changes.  Currently just the
        destructible flag.
        """
        wname = widget.get_name()
        (name, flagval, page) = wname.rsplit('_', 2)
        page = int(page)
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        self.on_flag_changed(name, flagval, widget, script)

    def populate_mapitem_button(self, num, page):
        widget = self.get_widget('item_%d_%d_text' % (num, page))
        imgwidget = self.get_widget('item_%d_%d_image' % (num, page))
        item = self.map.squares[self.sq_y][self.sq_x].scripts[page].items[num]
        self.populate_item_button(item, widget, imgwidget, self.get_widget('itemtable_%d' % (page)))

    def on_script_dropdown_changed(self, widget):
        """ Handle the trap dropdown change. """
        wname = widget.get_name()
        (varname, page) = wname.rsplit('_', 2)
        page = int(page)
        script = self.map.squares[self.sq_y][self.sq_x].scripts[page]
        script.__dict__[varname] = widget.get_active()

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
            items[num] = Item.new(c.book, True)
            items[num].tozero()
            self.register_mapitem_change(num, page)
        else:
            raise Exception('invalid action')

    def script_group_box(self, markup):
        box = gtk.VBox()
        box.show()
        header = gtk.Label()
        header.show()
        header.set_markup(markup)
        header.set_alignment(0, 0.5)
        header.set_padding(10, 7)
        box.pack_start(header, False, False)
        return box

    def append_script_notebook(self, script):
        """
        Given a script, adds a new tab to the script notebook, with
        all the necessary inputs.
        """
        square = self.map.squares[self.sq_y][self.sq_x]
        curpages = self.script_notebook.get_n_pages()

        # Label for the notebook
        label = gtk.Label('Object #%d' % (curpages+1))
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
        rm_txt = gtk.Label('Remove Object')
        rm_txt.show()
        rm_txt.set_padding(6, 0)
        remove_button_box.add(rm_txt)
        remove_button.add(remove_button_box)
        remove_align.add(remove_button)

        # Basic Information
        basic_box = self.script_group_box('<b>Basic Information</b>')
        binput = gtk.Table(10, 3)
        binput.show()
        spacer = gtk.Label('')
        spacer.show()
        spacer.set_padding(11, 0)
        binput.attach(spacer, 0, 1, 0, 10, gtk.FILL, gtk.FILL|gtk.EXPAND)
        basic_box.pack_start(binput, False, False)

        # Basic Inputs
        self.input_text(curpages, binput, 0, 'description', '(to update)',
                '(to update)')
        self.input_text(curpages, binput, 1, 'extratext', '(to update)',
                '(to update)')
        self.input_text(curpages, binput, 2, 'script', 'Script')

        # We special-case this to handle the weirdly-trapped door at (25, 26) in outpost
        if (square.scripts[curpages].trap in c.traptable.keys()):
            self.input_dropdown(curpages, binput, 4, 'trap', 'Trap', c.traptable.values(), None, self.on_script_dropdown_changed)
        else:
            self.input_uchar(curpages, binput, 4, 'trap', 'Trap', 'The trap value should be between 0 and 8 ordinarily.  The  current trap is undefined.')

        # We special-case this just in case
        if (square.scripts[curpages].state in c.containertable.keys()):
            self.input_dropdown(curpages, binput, 5, 'state', "State\n<i><small>(if container, door, or switch)</small></i>", c.containertable.values(), None, self.on_script_dropdown_changed)
        else:
            self.input_uchar(curpages, binput, 5, 'state', 'State', 'The state value should be between 0 and 5 ordinarily.  The current container state is undefined.')

        if c.book == 1:
            locktip = 'Zero is unlocked, 1 is the easiest lock, 60 is the highest in the game, and 99 denotes a slider lock'
        else:
            locktip = 'Zero is unlocked, 1 is the easiest lock, 10 is the highest in the game, and 12 denotes a slider lock'
        self.input_uchar(curpages, binput, 6, 'lock', 'Lock Level', locktip, self.on_locklevel_changed)

        if c.book == 1:
            # Book 1-specific values
            self.input_uchar(curpages, binput, 7, 'other', 'Other', 'When the Lock Level is set to 99, this is the combination of the safe.  Otherwise, it appears to be a value from 0 to 3.')

            # If we ever get more flags, this'll have to change
            if (square.scripts[curpages].flags & ~0x40 == 0):
                self.input_flag(curpages, binput, 8, 'flags', 0x40, 'Destructible')
            else:
                self.input_short(curpages, binput, 8, 'flags', 'Flags', 'Ordinarily this is a bit field, but the only value that I\'ve ever seen is "64" which denotes destructible.  Since this value is different, it\'s being shown here as an integer.')

            self.input_uchar(curpages, binput, 9, 'sturdiness', 'Sturdiness', '89 is the typical value for most objects.  Lower numbers are more flimsy.')
        else:
            # Book 2-specific values
            self.input_short(curpages, binput, 7, 'slider_loot', 'Slider/Lootlevel', 'If the container has a slider lock, this is the combination.  If not, it\'s the relative loot level (0 being appropriate to your class, 10 being the highest in-game)')
            self.input_uchar(curpages, binput, 8, 'on_empty', 'On-Empty', 'Typically 0 for permanent containers, 1 for bags.  There are a couple of exceptions')

            # Condition is special, we're using an hbox here
            scr = self.map.squares[self.sq_y][self.sq_x].scripts[curpages]
            self.input_label(curpages, binput, 9, 'cur_condition', 'Condition')
            hbox = gtk.HBox()
            curentry = gtk.SpinButton()
            self.register_widget('cur_condition_%d' % (curpages), curentry)
            curentry.set_range(0, 0xFFFFFFFF)
            curentry.set_adjustment(gtk.Adjustment(0, 0, 0xFFFFFFFF, 1, 10, 0))
            maxlabel = gtk.Label('out of:')
            self.register_widget('max_condition_%d_label' % (curpages), maxlabel)
            maxentry = gtk.SpinButton()
            self.register_widget('max_condition_%d' % (curpages), maxentry)
            maxentry.set_range(0, 0xFFFFFFFF)
            maxentry.set_adjustment(gtk.Adjustment(0, 0, 0xFFFFFFFF, 1, 10, 0))
            hbox.add(curentry)
            hbox.add(maxlabel)
            hbox.add(maxentry)
            if (script is not None):
                curentry.set_value(scr.cur_condition)
                maxentry.set_value(scr.max_condition)
            curentry.connect('value-changed', self.on_script_int_changed)
            maxentry.connect('value-changed', self.on_script_int_changed)
            align = gtk.Alignment(0, 0.5, 0, 1)
            align.add(hbox)
            align.show_all()
            binput.attach(align, 2, 3, 9, 10)

        # Contents
        contents_box = self.script_group_box('<b>Contents</b> <i>(If Container)</i>')
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

        # Unknowns
        unknown_box = self.script_group_box('<b>Unknowns</b>')
        uinput = gtk.Table(5, 3)
        uinput.show()
        spacer = gtk.Label('')
        spacer.show()
        spacer.set_padding(11, 0)
        uinput.attach(spacer, 0, 1, 0, 5, gtk.FILL, gtk.FILL|gtk.EXPAND)
        unknown_box.pack_start(uinput, False, False)

        # Data in Unknowns block
        if c.book == 1:
            self.input_short(curpages, uinput, 0, 'unknownh3', '<i>Unknown</i>')
            self.input_short(curpages, uinput, 1, 'zeroh1', '<i>Usually Zero 1</i>')
            self.input_int(curpages, uinput, 2, 'zeroi1', '<i>Usually Zero 2</i>')
            self.input_int(curpages, uinput, 3, 'zeroi2', '<i>Usually Zero 3</i>')
            self.input_int(curpages, uinput, 4, 'zeroi3', '<i>Usually Zero 4</i>')

        # Tab Content
        content = gtk.VBox()
        content.show()
        content.pack_start(remove_align, False, False)
        content.pack_start(basic_box, False, False)
        content.pack_start(contents_box, False, False)
        content.pack_start(unknown_box, False, False)

        # ... aand we should slap this all into a scrolledwindow
        sw = gtk.ScrolledWindow()
        sw.show()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vp = gtk.Viewport()
        vp.show()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(content)
        sw.add(vp)

        # Update our text labels and tooltips appropriately
        # for scriptid type 6
        self.update_script_type_strings(curpages, square.scriptid)

        # ... and update our "other" label
        self.on_locklevel_changed(self.get_widget('lock_%d' % (curpages)))

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

        # ... and possibly clean out our note
        self.update_object_note()

    def on_script_add(self, widget):
        """
        Called when a new script is added.  Creates a new
        Script object and handles adding it to the notebook.
        """
        square = self.map.squares[self.sq_y][self.sq_x]
        script = Mapscript.new(c.book, self.map.is_savegame())
        script.tozero(self.sq_x, self.sq_y)
        self.map.scripts.append(script)
        square.addscript(script)
        self.append_script_notebook(script)
        self.script_notebook.show()
        self.update_object_note()

    def on_healthmaxbutton_clicked(self, widget):
        """ Set the entity's health to its maximum. """
        entid = self.map.squares[self.sq_y][self.sq_x].entity.entid
        if (entid in c.entitytable):
            health = c.entitytable[entid].health
            self.get_widget('health').set_value(health)

    def on_setinitial_clicked(self, widget):
        """ Set the entity's "initial" location to the current (x,y) """
        ent = self.map.squares[self.sq_y][self.sq_x].entity
        ent.set_initial(self.sq_x, self.sq_y)
        self.get_widget('initial_loc').set_value(ent.initial_loc)

    def on_entity_toggle(self, widget):
        square = self.map.squares[self.sq_y][self.sq_x]
        if (square.entity is None):
            # create a new entity and toggle
            ent = Entity.new(c.book, self.map.is_savegame())
            ent.tozero(self.sq_x, self.sq_y)
            self.map.entities.append(ent)
            square.addentity(ent)
            self.populate_entity_tab(square)
            self.set_entity_toggle_button(False)
        else:
            # Remove the existing entity
            self.map.delentity(self.sq_x, self.sq_y)
            self.set_entity_toggle_button(True)

    def update_script_type_strings(self, page, scriptid):
        """
        Update the text for scripts on a single page, given the
        scriptid passed-in.
        """
        text_1 = self.get_widget('description_%d_label' % page)
        text_2 = self.get_widget('extratext_%d_label' % page)
        obj_1 = self.get_widget('description_%d' % page)
        obj_2 = self.get_widget('extratext_%d' % page)
        if (scriptid == 6):
            text_1.set_text('Map Link')
            text_2.set_text('Map Coordinates')
            obj_1.set_tooltip_text('Name of the map to send the player to.')
            obj_2.set_tooltip_text('The coordinates within the map specified above.  '
                'The coordinate "(56, 129)" would be written "12956"')
        else:
            text_1.set_text('Description')
            text_2.set_text('Extra Text')
            obj_1.set_tooltip_text('A basic description of the square.')
            obj_2.set_tooltip_text('More descriptive text (such as on signs or gravestones).')

    def update_all_scriptid_type_strings(self, square):
        """ Update the form text for all scripts on a square. """
        for idx in range(self.script_notebook.get_n_pages()):
            self.update_script_type_strings(idx, square.scriptid)

    def on_scriptid_changed(self, widget):
        """ Process changing our object/script ID. """
        self.on_singleval_square_changed_int(widget)
        square = self.map.squares[self.sq_y][self.sq_x]
        self.update_all_scriptid_type_strings(square)
        self.update_object_note()

    def on_scriptid_dd_changed(self, widget):
        """ Process changing our object/script type dropdown. """
        square = self.map.squares[self.sq_y][self.sq_x]
        square.scriptid = self.object_type_list_rev[widget.get_active()]
        self.update_all_scriptid_type_strings(square)
        self.update_object_note()

    def populate_squarewindow_from_square(self, square):
        """ Populates the square editing screen from a given square. """

        # Make sure we start out on the right page
        self.get_widget('square_notebook').set_current_page(0)

        # First the main items.  Wall stuff first.
        wallflags = ( 0x01, 0x04 )
        flagstotal = sum(map(int, wallflags))
        if (square.wall & ~flagstotal == 0):
            self.get_widget('wall_label').hide()
            self.get_widget('wall').hide()
            for flag in wallflags:
                self.get_widget('wall_%02X_label' % flag).show()
                self.get_widget('wall_%02X' % flag).show()
                if (square.wall & flag == flag):
                    self.get_widget('wall_%02X' % flag).set_active(True)
                else:
                    self.get_widget('wall_%02X' % flag).set_active(False)
        else:
            self.get_widget('wall_label').show()
            self.get_widget('wall').show()
            for flag in wallflags:
                self.get_widget('wall_%02X_label' % flag).hide()
                self.get_widget('wall_%02X' % flag).hide()
            self.get_widget('wall').set_value(square.wall)

        # ... and now the rest
        self.get_widget('floorimg').set_value(square.floorimg)
        self.get_widget('decalimg').set_value(square.decalimg)
        self.get_widget('wallimg').set_value(square.wallimg)
        self.get_widget('walldecalimg').set_value(square.walldecalimg)
        self.get_widget('unknown5').set_value(square.unknown5)

        # Now entites, if needed
        if (square.entity is None):
            self.set_entity_toggle_button(True)
        else:
            self.set_entity_toggle_button(False)
            self.populate_entity_tab(square)

        # ... and scripts (first the ID)
        if (square.scriptid in c.objecttypetable):
            self.get_widget('scriptid_num_align').hide()
            self.get_widget('scriptid_dd_align').show()
            self.get_widget('scriptid_dd').set_active(self.object_type_list[square.scriptid])
        else:
            self.get_widget('scriptid_num_align').show()
            self.get_widget('scriptid_dd_align').hide()
            self.get_widget('scriptid').set_value(square.scriptid)

        # ... now the scripts themselves.
        self.clear_script_notebook()
        if (len(square.scripts) > 0):
            for script in square.scripts:
                self.append_script_notebook(script)
            self.script_notebook.show()
        else:
            self.script_notebook.hide()

    def populate_entity_tab(self, square):
        """ Populates the entity tab of the square editing screen. """
        if (square.entity.entid in c.entitytable):
            if (c.entitytable[square.entity.entid].name in self.entitykeys):
                idx = self.entitykeys.index(c.entitytable[square.entity.entid].name)
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
        self.get_widget('entscript').set_text(square.entity.entscript)
        if (self.map.is_savegame()):
            self.get_widget('friendly').set_value(square.entity.friendly)
            self.get_widget('health').set_value(square.entity.health)
            self.get_widget('unknownc1').set_value(square.entity.unknownc1)
            self.get_widget('ent_zero1').set_value(square.entity.ent_zero1)
            self.get_widget('initial_loc').set_value(square.entity.initial_loc)
            if c.book == 1:
                self.get_widget('unknownc2').set_value(square.entity.unknownc2)
                self.get_widget('ent_zero2').set_value(square.entity.ent_zero2)
            else:
                self.get_widget('movement').set_value(square.entity.movement)

    def update_object_note(self):
        """
        Updates our object note, to let the user know if there should
        be an object or not.
        """
        square = self.map.squares[self.sq_y][self.sq_x]
        note = self.get_widget('object_note')
        if (len(square.scripts) > 1):
            note.set_markup('<b>Warning:</b> There are three instances in the master map files where more than one object is defined for a tile, but doing so is discouraged.  Only one of the objects will actually be used by the game engine.')
            note.show()
        elif (square.scriptid > 0 and square.scriptid < 25):
            if (len(square.scripts) > 0):
                note.hide()
            else:
                note.set_markup('<b>Note:</b> Given the object type specified above, an object should be created for this tile.')
                note.show()
        else:
            if (len(square.scripts) > 0):
                note.set_markup('<b>Note:</b> Given the object type specified above, this tile should <i>not</i> have an object.')
                note.show()
            else:
                note.hide()

    def open_floorsel(self, widget):
        """ Show the floor selection window. """
        self.imgsel_launch(self.get_widget('floorimg'),
                self.gfx.square_width, self.gfx.square_height, self.gfx.floor_cols, self.gfx.floor_rows,
                self.gfx.get_floor, True, 1)

    def open_draw_floorsel(self, widget):
        """ Show the floor selection window for our drawing widget. """
        self.imgsel_launch(self.draw_floor_spin,
                self.gfx.square_width, self.gfx.square_height, self.gfx.floor_cols, self.gfx.floor_rows,
                self.gfx.get_floor, True, 1)

    def open_decalsel(self, widget):
        """ Show the decal selection window. """
        self.imgsel_launch(self.get_widget('decalimg'),
                self.gfx.square_width, self.gfx.square_height, self.gfx.decal_cols, self.gfx.decal_rows,
                self.gfx.get_decal, True, 1)

    def open_draw_decalsel(self, widget):
        """ Show the decal selection window for our drawing widget. """
        self.imgsel_launch(self.draw_decal_spin,
                self.gfx.square_width, self.gfx.square_height, self.gfx.decal_cols, self.gfx.decal_rows,
                self.gfx.get_decal, True, 1)

    def open_walldecalsel(self, widget):
        """ Show the wall decal selection window. """
        self.imgsel_launch(self.get_widget('walldecalimg'),
                self.gfx.square_width, self.gfx.square_height*3, self.gfx.walldecal_cols, self.gfx.walldecal_rows,
                self.gfx.get_object_decal, True, 1)

    def open_draw_walldecalsel(self, widget):
        """ Show the walldecal selection window for our drawing widget. """
        self.imgsel_launch(self.draw_walldecal_spin,
                self.gfx.square_width, self.gfx.square_height*3, self.gfx.walldecal_cols, self.gfx.walldecal_rows,
                self.gfx.get_object_decal, True, 1)

    def objsel_fix_pixbuf(self, pixbuf):
        """ Function to fix the pixbuf, for object loading. """
        return pixbuf[0]

    def open_objsel(self, widget, spinwidget=None):
        """
        Launch our object selection window.  This is effectively
        an override of imgsel_launch() - we'll be playing some games
        to reduce code duplication here.  This should probably be
        in a class, somehow, instead of a dict.
        """
        if c.book == 1:
            self.get_widget('imgsel_scroll1').show()
            letters = ['d', 'c', 'b', 'a']
            self.get_widget('objsel_a_title_label').set_label('Set A (misc)')
            self.get_widget('objsel_b_title_label').set_label('Set B (misc)')
            self.get_widget('objsel_c_title_label').set_label('Set C (walls)')
            self.get_widget('objsel_d_title_label').set_label('Set D (trees)')
        else:
            self.get_widget('imgsel_scroll1').hide()
            letters = ['c', 'd', 'a']
            self.get_widget('objsel_a_title_label').set_label('Set A (misc)')
            self.get_widget('objsel_c_title_label').set_label('Set B (walls)')
            self.get_widget('objsel_d_title_label').set_label('Set C (trees)')
        self.imgsel_window = self.get_widget('objselwindow')
        self.imgsel_window.set_size_request((self.gfx.obj_a_width*self.gfx.obj_a_cols)+60, 600)
        if (spinwidget is None):
            self.imgsel_widget = self.get_widget('wallimg')
        else:
            self.imgsel_widget = spinwidget
        self.objsel_book = self.get_widget('objsel_book')
        self.imgsel_bgcolor_img = self.get_widget('objsel_bgcolor_img')
        self.imgsel_bgcolor_event = self.get_widget('objsel_bgcolor_event')
        self.imgsel_getfunc = self.gfx.get_object
        self.imgsel_getfunc_obj_func = None
        self.imgsel_getfunc_extraarg = self.map.tree_set
        self.imgsel_pixbuffunc = self.objsel_fix_pixbuf
        self.imgsel_init_bgcolor()
        self.imgsel_blank_color = self.imgsel_generate_grayscale(127)
        self.objsel_panes = {}
        self.objsel_panes['a'] = {
                'init': False,
                'clean': [],
                'area': self.get_widget('objsel_a_area'),
                'width': self.gfx.obj_a_width,
                'height': self.gfx.obj_a_height,
                'cols': self.gfx.obj_a_cols,
                'rows': self.gfx.obj_a_rows,
                'x': self.gfx.obj_a_width*self.gfx.obj_a_cols,
                'y': self.gfx.obj_a_height*self.gfx.obj_a_rows,
                'offset': self.gfx.obj_a_offset,
                'mousex': -1,
                'mousey': -1,
                'mousex_prev': -1,
                'mousey_prev': -1,
                'blank': None,
                'page': 0,
            }
        if c.book == 1:
            self.objsel_panes['b'] = {
                    'init': False,
                    'clean': [],
                    'area': self.get_widget('objsel_b_area'),
                    'width': self.gfx.obj_b_width,
                    'height': self.gfx.obj_b_height,
                    'cols': self.gfx.obj_b_cols,
                    'rows': self.gfx.obj_b_rows,
                    'x': self.gfx.obj_b_width*self.gfx.obj_b_cols,
                    'y': self.gfx.obj_b_height*self.gfx.obj_b_rows,
                    'offset': self.gfx.obj_b_offset,
                    'mousex': -1,
                    'mousey': -1,
                    'mousex_prev': -1,
                    'mousey_prev': -1,
                    'blank': None,
                    'page': 1,
                }
        self.objsel_panes['c'] = {
                'init': False,
                'clean': [],
                'area': self.get_widget('objsel_c_area'),
                'width': self.gfx.obj_c_width,
                'height': self.gfx.obj_c_height,
                'cols': self.gfx.obj_c_cols,
                'rows': self.gfx.obj_c_rows,
                'x': self.gfx.obj_c_width*self.gfx.obj_c_cols,
                'y': self.gfx.obj_c_height*self.gfx.obj_c_rows,
                'offset': self.gfx.obj_c_offset,
                'mousex': -1,
                'mousey': -1,
                'mousex_prev': -1,
                'mousey_prev': -1,
                'blank': None,
                'page': 2,
            }
        self.objsel_panes['d'] = {
                'init': False,
                'clean': [],
                'area': self.get_widget('objsel_d_area'),
                'width': self.gfx.obj_d_width,
                'height': self.gfx.obj_d_height,
                'cols': self.gfx.obj_d_cols,
                'rows': self.gfx.obj_d_rows,
                'x': self.gfx.obj_d_width*self.gfx.obj_d_cols,
                'y': self.gfx.obj_d_height*self.gfx.obj_d_rows,
                'offset': self.gfx.obj_d_offset,
                'mousex': -1,
                'mousey': -1,
                'mousex_prev': -1,
                'mousey_prev': -1,
                'blank': None,
                'page': 3,
            }
        # Set initial page
        curpage = 0
        for letter in letters:
            if (self.imgsel_widget.get_value_as_int() >= self.objsel_panes[letter]['offset']):
                curpage = self.objsel_panes[letter]['page']
                break
        self.objsel_book.set_current_page(curpage)
        self.objsel_current = ''
        #self.load_objsel_vars(self.get_widget('objsel_%s_area' % (letters[3-curpage])))
        self.imgsel_window.show()

    def open_draw_objsel(self, widget):
        """ Show the wall selection window for our drawing widget. """
        self.open_objsel(widget, self.draw_wall_spin)

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

    def draw_erase_toggle(self, to_draw=True):
        if to_draw:
            self.get_widget('draw_frame').show()
            self.get_widget('erase_frame').hide()
        else:
            self.get_widget('draw_frame').hide()
            self.get_widget('erase_frame').show()

    def update_activity_label(self, widget=None):
        newlabel = ''
        if self.ctl_edit_toggle.get_active():
            newlabel = 'Editing Single Tiles'
        elif self.ctl_move_toggle.get_active():
            newlabel = 'Scrolling Map'
        elif self.ctl_draw_toggle.get_active():
            self.draw_erase_toggle(True)
            elems = []
            if (self.draw_floor_checkbox.get_active()):
                elems.append('Floors')
            if (self.draw_decal_checkbox.get_active()):
                elems.append('Decals')
            if (self.draw_wall_checkbox.get_active()):
                elems.append('Walls')
            if (self.draw_walldecal_checkbox.get_active()):
                elems.append('Wall Decals')
            if (self.draw_barrier.get_active()):
                elems.append('Barriers')
            if (len(elems) > 0):
                newlabel = 'Drawing %s' % (', '.join(elems))
            else:
                newlabel = 'Drawing (no elements selected)'
        elif self.ctl_erase_toggle.get_active():
            self.draw_erase_toggle(False)
            elems = []
            if (self.erase_floor_checkbox.get_active()):
                elems.append('Floors')
            if (self.erase_decal_checkbox.get_active()):
                elems.append('Decals')
            if (self.erase_wall_checkbox.get_active()):
                elems.append('Walls')
            if (self.erase_walldecal_checkbox.get_active()):
                elems.append('Wall Decals')
            if (self.erase_barrier.get_active()):
                elems.append('Barriers')
            if (len(elems) > 0):
                newlabel = 'Erasing %s' % (', '.join(elems))
            else:
                newlabel = 'Erasing (no elements selected)'
        else:
            newlabel = '<i>Unknown</i>'
        self.activity_label.set_markup('Activity: %s' % (newlabel))

    def on_control_toggle(self, widget):
        clicked = widget.get_name()
        if (widget.get_active()):
            if (clicked == 'ctl_edit_toggle'):
                self.edit_mode = self.MODE_EDIT
            elif (clicked == 'ctl_move_toggle'):
                self.edit_mode = self.MODE_MOVE
            elif (clicked == 'ctl_draw_toggle'):
                self.edit_mode = self.MODE_DRAW
            elif (clicked == 'ctl_erase_toggle'):
                self.edit_mode = self.MODE_ERASE
            else:
                # TODO: Except here or something
                print "Unknown control toggled, should never get here"
            self.maparea.window.set_cursor(self.cursor_map[self.edit_mode])
            self.update_activity_label()

    def on_clicked(self, widget, event):
        """ Handle a mouse click. """
        # TODO: verify button numbers on, say, non-three-button mice
        if (event.button not in self.mouse_action_maps[self.edit_mode]):
            return

        action = self.mouse_action_maps[self.edit_mode][event.button]
        if (action == self.ACTION_DRAG):
            adjust = self.mainscroll.get_hadjustment()
            self.dragging = True
            self.hold_x = event.x_root
            self.hold_y = event.y_root
            self.diff_x = 0
            self.diff_y = 0
            self.maparea.window.set_cursor(self.cursor_move_drag)
        if (action == self.ACTION_EDIT):
            if (self.sq_y < len(self.map.squares)):
                if (self.sq_x < len(self.map.squares[self.sq_y])):
                    self.undo.store(self.sq_x, self.sq_y)
                    self.populate_squarewindow_from_square(self.map.squares[self.sq_y][self.sq_x])
                    self.get_widget('squarelabel').set_markup('<b>Map Tile (%d, %d)</b>' % (self.sq_x, self.sq_y))
                    self.squarewindow.show()
        elif (action == self.ACTION_DRAW):
            self.drawing = True
            self.action_draw_square(self.sq_x, self.sq_y)
        elif (action == self.ACTION_ERASE):
            self.erasing = True
            self.action_erase_square(self.sq_x, self.sq_y)
        #else:
        #    # Book 2 stupid reporting (for now)
        #    square = self.map.squares[self.sq_y][self.sq_x]
        #    if square:
        #        print "Square at (%d, %d)" % (self.sq_x, self.sq_y)
        #        print "   Barrier Flag: %d" % (square.wall)
        #        print "   Floor: %d" % (square.floorimg)
        #        print "   Decal: %d" % (square.decalimg)
        #        print "   Wall: %d" % (square.wallimg)
        #        print "   Wall Decal: %d" % (square.walldecalimg)
        #        print "   Unknown: %d" % (square.unknown5)
        #        print "   Script ID: %d" % (square.scriptid)
        #        if len(square.scripts) > 0:
        #            for (i, script) in enumerate(square.scripts):
        #                print "   Script %d:" % (i+1)
        #                print script.display()
        #                print
        #        elif square.scriptid != 0:
        #            print "   No script object!"
        #        if square.entity:
        #            print
        #            print "   Entity:"
        #            print square.entity.display()
        #        print

    def on_released(self, widget=None, event=None):
        if (self.dragging or self.drawing or self.erasing):
            self.dragging = False
            self.drawing = False
            self.erasing = False
            self.maparea.window.set_cursor(self.cursor_map[self.edit_mode])

    def action_draw_square(self, x, y):
        """ What to do when we're drawing on a square on the map."""

        # First store our undo state
        self.undo.store(x, y)
        self.undo.set_text('Draw')
        
        try:
            # Grab our square object
            square = self.map.squares[y][x]

            # Now draw anything that the user's requesed
            if (self.draw_floor_checkbox.get_active()):
                square.floorimg = self.draw_floor_spin.get_value_as_int()
            if (self.draw_decal_checkbox.get_active()):
                square.decalimg = self.draw_decal_spin.get_value_as_int()
            if (self.draw_wall_checkbox.get_active()):
                square.wallimg = self.draw_wall_spin.get_value_as_int()
            if (self.draw_walldecal_checkbox.get_active()):
                square.walldecalimg = self.draw_walldecal_spin.get_value_as_int()

            # Check to see if we should change the "wall" flag
            if (self.draw_barrier.get_active()):
                if (self.draw_barrier_seethrough.get_active()):
                    square.wall = 5
                else:
                    square.wall = 1
            elif (self.smartdraw_check.get_active() and self.draw_smart_barrier.get_active()):
                # TODO: it would be nice to check to see if we really should be updating
                # barriers here...  as it is, if you leave all the "drawing" checkboxes off
                # but draw around, this function will update barrier information as it goes.
                # Ah well.  For now I'm just going to let it do that.
                #if (self.draw_wall_checkbox.get_active() or self.draw_floor_checkbox.get_active() or
                #        self.draw_decal_checkbox.get_active()):
                if (square.walldecalimg in c.wall_list['walldecal_seethrough']):
                    square.wall = 5
                elif (square.wallimg in c.wall_list['wall_blocked']):
                    square.wall = 1
                elif (square.wallimg in c.wall_list['wall_seethrough']):
                    square.wall = 5
                elif (square.decalimg in c.wall_list['decal_blocked']):
                    square.wall = 1
                elif (square.decalimg in c.wall_list['decal_seethrough']):
                    square.wall = 5
                elif (square.floorimg in c.wall_list['floor_seethrough']):
                    square.wall = 5
                else:
                    square.wall = 0

            # Handle "smart" walls if requested
            if (self.draw_wall_checkbox.get_active() and self.smartdraw_check.get_active() and self.draw_smart_wall.get_active()):
                for dir in [Map.DIR_NE, Map.DIR_SE, Map.DIR_SW, Map.DIR_NW]:
                    self.undo.add_additional(self.map.square_relative(x, y, dir))
                affected_squares = self.smartdraw.draw_wall(square)
                if (affected_squares is not None):
                    self.undo.set_text('Smart Wall Draw')
                    for adjsquare in affected_squares:
                        self.redraw_square(adjsquare.x, adjsquare.y)
            if (self.draw_wall_checkbox.get_active() and self.smartdraw_check.get_active() and self.smart_complex_objects.get_active()):
                (text, affected_squares) = self.smartdraw.draw_smart_complex_wall(square, self.undo)
                if (text is not None):
                    self.undo.set_text('Smart Wall Draw (%s)' % (text))
                    for adjsquare in affected_squares:
                        self.redraw_square(adjsquare.x, adjsquare.y)

            # Handle "smart" floors if needed
            if (self.draw_floor_checkbox.get_active() and
                    not self.draw_decal_checkbox.get_active() and
                    self.smartdraw_check.get_active() and
                    self.draw_smart_floor.get_active()):
                for dir in [Map.DIR_NE, Map.DIR_E, Map.DIR_SE, Map.DIR_S, Map.DIR_SW, Map.DIR_W, Map.DIR_NW, Map.DIR_N]:
                    self.undo.add_additional(self.map.square_relative(x, y, dir))
                affected_squares = self.smartdraw.draw_floor(square, self.draw_straight_paths.get_active())
                if (affected_squares is not None):
                    self.undo.set_text('Smart Draw')
                    for adjsquare in affected_squares:
                        self.redraw_square(adjsquare.x, adjsquare.y)
            if (self.draw_floor_checkbox.get_active() and self.smartdraw_check.get_active() and self.smart_complex_objects.get_active()):
                (text, affected_squares) = self.smartdraw.draw_smart_complex_floor(square, self.undo)
                if (text is not None):
                    self.undo.set_text('Smart Draw (%s)' % (text))
                    for adjsquare in affected_squares:
                        self.redraw_square(adjsquare.x, adjsquare.y)

            # Handles "smart" decals if needed
            if (self.draw_walldecal_checkbox.get_active() and self.smartdraw_check.get_active() and self.draw_smart_walldecal.get_active()):
                self.smartdraw.draw_walldecal(square)

            # And then close off our undo and redraw if needed
            if (self.undo.finish()):
                self.redraw_square(x, y)
                self.update_undo_gui()

        except Exception:

            # Report our Exception to the user (let it go to stderr as well)
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, file=sys.stderr)
            exceptionStr = ''.join(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
            buf = self.map_exception_view.get_buffer()
            buf.set_text(exceptionStr)
            buf.place_cursor(buf.get_start_iter())
            self.map_exception_window.run()
            self.map_exception_window.hide()
            
            # Cancel out of the Undo so that the app isn't locked up
            # TODO: *should* we try to finish the undo instead, so it may be able
            # to back out *some* data at least?
            self.undo.cancel()

            # Redraw our square anyway, just in case changes have taken place
            # anyway
            self.redraw_square(x, y)

            # Reset our state vars (this generally won't happen automatically, because
            # we arrested the mouse with the new window)
            self.on_released()

    def action_erase_square(self, x, y):
        """ What to do when we're erasing on a square on the map."""

        # TODO: Figure out if we really should do any of the smartdraw
        # stuff here.  I'm not so sure.  And anyway, I suspect that
        # it may be not processing that stuff anyway right now.

        # First store our undo state
        self.undo.store(x, y)
        self.undo.set_text('Erase')
        
        # Grab our square object
        square = self.map.squares[y][x]

        # Now erase anything that the user's requesed
        if (self.erase_barrier.get_active()):
            square.wall = 0
        if (self.erase_floor_checkbox.get_active()):
            if (self.smartdraw_check.get_active() and self.draw_smart_barrier.get_active()):
                if (square.floorimg in c.wall_list['floor_seethrough']):
                    square.wall = 0
            square.floorimg = 0
        if (self.erase_decal_checkbox.get_active()):
            if (self.smartdraw_check.get_active() and self.draw_smart_barrier.get_active()):
                if (square.decalimg in c.wall_list['decal_blocked']+c.wall_list['decal_seethrough']):
                    square.wall = 0
            square.decalimg = 0
        if (self.erase_wall_checkbox.get_active()):
            if (self.smartdraw_check.get_active() and self.draw_smart_barrier.get_active()):
                if (square.wallimg in c.wall_list['wall_blocked']+c.wall_list['wall_seethrough']):
                    square.wall = 0
            square.wallimg = 0
        if (self.erase_walldecal_checkbox.get_active()):
            square.walldecalimg = 0

        # Handle "smart" walls if requested
        if (self.draw_wall_checkbox.get_active() and self.smartdraw_check.get_active() and self.draw_smart_wall.get_active()):
            for dir in [Map.DIR_NE, Map.DIR_SE, Map.DIR_SW, Map.DIR_NW]:
                self.undo.add_additional(self.map.square_relative(x, y, dir))
            affected_squares = self.smartdraw.draw_wall(square)
            if (affected_squares is not None):
                self.undo.set_text('Smart Wall Erase')
                for adjsquare in affected_squares:
                    self.redraw_square(adjsquare.x, adjsquare.y)

        # Handle "smart" floors if needed
        if (self.erase_floor_checkbox.get_active() and
                not self.erase_decal_checkbox.get_active() and
                self.smartdraw_check.get_active() and
                self.draw_smart_floor.get_active()):
            for dir in [Map.DIR_NE, Map.DIR_E, Map.DIR_SE, Map.DIR_S, Map.DIR_SW, Map.DIR_W, Map.DIR_NW, Map.DIR_N]:
                self.undo.add_additional(self.map.square_relative(x, y, dir))
            affected_squares = self.smartdraw.draw_floor(square, self.draw_straight_paths.get_active())
            if (affected_squares is not None):
                self.undo.set_text('Smart Erase')
                for adjsquare in affected_squares:
                    self.redraw_square(adjsquare.x, adjsquare.y)

        # Handles "smart" wall decals if needed
        # This just randomizes, so don't bother here.
        #if (self.erase_walldecal_checkbox.get_active() and self.smartdraw_check.get_active() and self.draw_smart_walldecal.get_active()):
        #    self.smartdraw.draw_walldecal(square)

        # And then close off our undo and redraw if needed
        if (self.undo.finish()):
            self.redraw_square(x, y)
            self.update_undo_gui()

    def map_toggle(self, widget):
        if not self.updating_map_checkboxes:
            self.draw_map()

    def mass_update_checkboxes(self, status, checkboxes):
        self.updating_map_checkboxes = True
        changed = False
        for elem in checkboxes:
            if (elem.get_active() != status):
                changed = True
                elem.set_active(status)
        self.updating_map_checkboxes = False
        if changed:
            self.draw_map()

    def draw_check_set_to(self, status):
        return self.mass_update_checkboxes(status, [self.floor_toggle, self.decal_toggle, self.object_toggle,
            self.wall_toggle, self.tree_toggle, self.objectdecal_toggle, self.entity_toggle, self.huge_gfx_toggle])

    def draw_check_all(self, widget):
        self.draw_check_set_to(True)

    def draw_uncheck_all(self, widget):
        self.draw_check_set_to(False)

    def highlight_check_set_to(self, status):
        return self.mass_update_checkboxes(status, [self.barrier_hi_toggle, self.script_hi_toggle, self.entity_hi_toggle])

    def highlight_check_all(self, widget):
        self.highlight_check_set_to(True)

    def highlight_uncheck_all(self, widget):
        self.highlight_check_set_to(False)

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
            if self.req_book == 1 or self.map.is_savegame():
                if (square.entity.friendly == 1):
                    entity = (0, 1, 0, 0.5)
                else:
                    entity = (1, 0, 0, 0.5)
            else:
                if square.entity.entid in c.entitytable:
                    if c.entitytable[square.entity.entid].friendly == 1:
                        entity = (0, 1, 0, 0.5)
                    else:
                        entity = (1, 0, 0, 0.5)
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
        elif (square.floorimg == 126 and not self.floor_toggle.get_active()):
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
            main_ctx.rectangle(x1-self.z_squarebuf_offset, top, self.z_squarebuf_w, height)
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
                sq_ctx.set_source_surface(pixbuf, self.z_squarebuf_offset, self.z_4xheight)
                sq_ctx.paint()
                drawn = True

        # Draw the floor decal
        if (self.decal_toggle.get_active()):
            pixbuf = self.gfx.get_decal(square.decalimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, self.z_squarebuf_offset, self.z_4xheight)
                sq_ctx.paint()
                drawn = True
                # Check to see if we should draw a flame
                if ((self.req_book == 1 and square.decalimg == 52) or
                    (self.req_book == 2 and square.decalimg == 101)):
                    pixbuf = self.gfx.get_flame(self.curzoom)
                    if (pixbuf is not None):
                        # TODO: in book 2, campfire wall objects will overwrite some of our campfire flame
                        # (note that the campfire wall object will NOT provide an in-game flame on its own)
                        xoffset = self.z_halfwidth-int(pixbuf.get_width()/2)+self.z_squarebuf_offset
                        yoffset = int(self.z_height*0.4)
                        sq_ctx.set_source_surface(pixbuf, xoffset, self.z_3xheight+yoffset)
                        sq_ctx.paint()

        wallid = square.wallimg
        try:
            walltype = self.gfx.wall_types[wallid]
        except KeyError:
            # This should only happen for Book 2 maps, and should only
            # denote that it's one of the gigantic graphic maps.
            print 'Unknown wall type %d' % (wallid)
            walltype = self.gfx.TYPE_NONE

        # Draw the object
        if (self.object_toggle.get_active() and walltype == self.gfx.TYPE_OBJ):
            (pixbuf, pixheight, offset) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, offset+self.z_squarebuf_offset, self.z_height*(4-pixheight))
                sq_ctx.paint()
                drawn = True

        # Draw a zapper
        if (self.req_book == 2 and self.object_toggle.get_active() and square.scriptid == 19):
            pixbuf = self.gfx.get_zapper(self.curzoom)
            if pixbuf is not None:
                xoffset = self.z_squarebuf_offset
                yoffset = 0
                sq_ctx.set_source_surface(pixbuf, xoffset, self.z_3xheight+yoffset)
                sq_ctx.paint()

        # Draw walls
        if (self.wall_toggle.get_active() and walltype == self.gfx.TYPE_WALL):
            (pixbuf, pixheight, offset) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, offset+self.z_squarebuf_offset, self.z_height*(4-pixheight))
                sq_ctx.paint()
                drawn = True
                # TODO: this object should really be a TYPE_OBJ instead...
                if (self.req_book == 2 and (square.wallimg == 349 or square.wallimg == 350)):
                    pixbuf = self.gfx.get_flame(self.curzoom)
                    if (pixbuf is not None):
                        xoffset = self.z_halfwidth-int(pixbuf.get_width()/2)+self.z_squarebuf_offset
                        yoffset = int(self.z_height*0.3)
                        sq_ctx.set_source_surface(pixbuf, xoffset, self.z_height+yoffset)
                        sq_ctx.paint()

        # Draw trees
        if (self.tree_toggle.get_active() and walltype == self.gfx.TYPE_TREE):
            (pixbuf, pixheight, offset) = self.gfx.get_object(wallid, self.curzoom, False, self.map.tree_set)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, offset+self.z_squarebuf_offset, self.z_height*(4-pixheight))
                sq_ctx.paint()
                drawn = True

        # Draw the object decal
        if (self.objectdecal_toggle.get_active()):
            pixbuf = self.gfx.get_object_decal(square.walldecalimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, self.z_squarebuf_offset, self.z_2xheight)
                sq_ctx.paint()
                drawn = True
                # Check to see if we should draw a flame
                if ((self.req_book == 1 and (square.walldecalimg == 17 or square.walldecalimg == 18)) or
                    (self.req_book == 2 and (square.walldecalimg == 2 or square.walldecalimg == 4))):
                    pixbuf = self.gfx.get_flame(self.curzoom)
                    if (pixbuf is not None):
                        xoffset = int(pixbuf.get_width()*0.3)
                        yoffset = int(self.z_height/4)
                        if (self.req_book == 2):
                            yoffset -= 1
                        if (square.walldecalimg == 17 or square.walldecalimg == 2):
                            sq_ctx.set_source_surface(pixbuf, self.curzoom-pixbuf.get_width()-xoffset+self.z_squarebuf_offset, self.z_2xheight+yoffset)
                        else:
                            sq_ctx.set_source_surface(pixbuf, xoffset+self.z_squarebuf_offset, self.z_2xheight+yoffset)
                        sq_ctx.paint()

        # Draw the entity if needed
        # We switch to using op_ctx and op_surf because we may not be drawing on sq_ctx
        # from this point on, depending on entity width
        op_surf = self.squarebuf
        op_ctx = sq_ctx
        op_xoffset = 0
        if (square.entity is not None and self.entity_toggle.get_active()):
            ent_img = self.gfx.get_entity(square.entity.entid, square.entity.direction, self.curzoom)
            if (ent_img is not None):
                if (ent_img.get_width() > self.z_squarebuf_w):
                    # This whole bit here will copy our squarebuf into a larger surface, centered
                    # (so, transparent on the side)
                    self.ent_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, ent_img.get_width(), self.z_5xheight)
                    self.ent_ctx = cairo.Context(self.ent_surf)
                    op_xoffset = int((ent_img.get_width()-self.z_squarebuf_w)/2)
                    self.ent_ctx.set_source_surface(op_surf, op_xoffset, 0)
                    self.ent_ctx.paint()
                    op_surf = self.ent_surf
                    op_ctx = self.ent_ctx
                if (op_surf.get_width() > ent_img.get_width()):
                    offset = int((op_surf.get_width() - ent_img.get_width())/2)
                else:
                    offset = 0
                op_ctx.set_source_surface(ent_img, offset, self.z_5xheight-ent_img.get_height())
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
                main_ctx.set_source_surface(op_surf, x1-op_xoffset-self.z_squarebuf_offset, top-buftop)
                main_ctx.paint()
            else:
                # This is only for the initial map population
                self.guicache_ctx.set_source_surface(op_surf, x1-op_xoffset-self.z_squarebuf_offset, top-buftop)
                self.guicache_ctx.paint()

        return (op_surf, op_xoffset+self.z_squarebuf_offset)

    def draw_huge_gfx(self, square):
        """
        Draws a "huge" graphic image on our map (like Hammerlorne, etc).
        Only used in Book 2.
        """
        if square.scriptid == 21 and len(square.scripts) > 0:
            img = self.gfx.get_huge_gfx(square.scripts[0].extratext, self.curzoom)
            if img:
                #img.write_to_png('test_%s' % (square.scripts[0].extratext))

                x = square.x
                y = square.y
                # TODO: xpad processing should be abstracted somehow when we're drawing whole rows
                # (for instance, when initially loading the map)
                if (y % 2 == 1):
                    xpad = self.z_halfwidth
                else:
                    xpad = 0

                xstart = (x*self.z_width)+xpad - int(img.get_width()/2) + self.z_height
                ystart = y*self.z_halfheight + self.z_height

                self.guicache_ctx.set_source_surface(img, xstart, ystart-img.get_height())
                self.guicache_ctx.paint()

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
            if ((self.req_book == 1 and square.decalimg == 52) or
                (self.req_book == 2 and square.decalimg == 101)):
                pixbuf = self.gfx.get_flame(52, True)
                if (pixbuf is not None):
                    pixbuf.composite(comp_pixbuf, 17, 88, 18, 30, 17, 88, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
        if (square.wallimg > 0):
            (pixbuf, pixheight, offset) = self.gfx.get_object(square.wallimg, 52, True, self.map.tree_set)
            if (pixbuf is not None):
                pixbuf.composite(comp_pixbuf, 0, 26*(4-pixheight), 52, 26*(pixheight+1), 0, 26*(4-pixheight), 1, 1, gtk.gdk.INTERP_NEAREST, 255)
            if (self.req_book == 2 and (square.wallimg == 349 or square.wallimg == 350)):
                pixbuf = self.gfx.get_flame(52, True)
                if (pixbuf is not None):
                    pixbuf.composite(comp_pixbuf, 17, 35, 18, 30, 17, 35, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
        if (square.walldecalimg > 0):
            pixbuf = self.gfx.get_object_decal(square.walldecalimg, 52, True)
            if (pixbuf is not None):
                pixbuf.composite(comp_pixbuf, 0, 52, 52, 78, 0, 52, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
            if ((self.req_book == 1 and (square.walldecalimg == 17 or square.walldecalimg == 18)) or
                (self.req_book == 2 and (square.walldecalimg == 2 or square.walldecalimg == 4))):
                pixbuf = self.gfx.get_flame(52, True)
                if (pixbuf is not None):
                    if (square.walldecalimg == 17):
                        pixbuf.composite(comp_pixbuf, 29, 58, 18, 30, 29, 58, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
                    elif (square.walldecalimg == 18):
                        pixbuf.composite(comp_pixbuf, 5, 58, 18, 30, 5, 58, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
                    elif (square.walldecalimg == 2):
                        pixbuf.composite(comp_pixbuf, 29, 58, 18, 30, 29, 58, 1, 1, gtk.gdk.INTERP_NEAREST, 255)
                    else:
                        pixbuf.composite(comp_pixbuf, 5, 58, 18, 30, 5, 58, 1, 1, gtk.gdk.INTERP_NEAREST, 255)

        # ... and update the main image
        self.get_widget('composite_area').set_from_pixbuf(comp_pixbuf)

    def export_map_pngs(self):
        """
        A little sub to loop through and write out a PNG of each mapname
        """
        # TODO: keep?  throw away?
        self.mapinit = True
        self.set_zoom_vars(1)
        print self.options
        for file in self.options['filenames']:
            self.load_from_file(file)
            #self.draw_map()
            (pngfile, junk) = file.split('.')
            pngfile = '%s.png' % (pngfile)
            self.guicache.write_to_png(pngfile)
        import sys
        sys.exit(0)
        return False

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

        self.squarebuf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_squarebuf_w, self.z_5xheight)
        self.squarebuf_ctx = cairo.Context(self.squarebuf)
        self.guicache = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_mapsize_x, self.z_mapsize_y)
        self.guicache_ctx = cairo.Context(self.guicache)
        self.guicache_ctx.set_source_rgba(0, 0, 0, 1)
        self.guicache_ctx.paint()

        self.ent_surf = None
        self.ent_ctx = None

        # Activate (or deactivate) our "draw barrier" checkboxes depending on if we're highlighting
        # barriers or not
        if (self.barrier_hi_toggle.get_active()):
            self.draw_barrier.set_sensitive(True)
            self.draw_barrier_seethrough.set_sensitive(True)
            self.erase_barrier.set_sensitive(True)
        else:
            self.draw_barrier.set_sensitive(False)
            self.draw_barrier.set_active(False)
            self.draw_barrier_seethrough.set_sensitive(False)
            self.draw_barrier_seethrough.set_active(False)
            self.erase_barrier.set_sensitive(False)

        # Set up a "blank" tile to draw everything else on top of
        self.blanksquare = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_squarebuf_w, self.z_5xheight)
        sq_ctx = cairo.Context(self.blanksquare)
        sq_ctx.save()
        sq_ctx.set_operator(cairo.OPERATOR_CLEAR)
        sq_ctx.paint()
        sq_ctx.restore()

        # Set up a default square with just a black tile, for otherwise-empty tiles
        self.basicsquare = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_squarebuf_w, self.z_5xheight)
        basic_ctx = cairo.Context(self.basicsquare)
        basic_ctx.set_source_rgba(0, 0, 0, 1)
        basic_ctx.move_to(self.z_squarebuf_offset+0, self.z_4xheight+self.z_halfheight)
        basic_ctx.line_to(self.z_squarebuf_offset+self.z_halfwidth, self.z_4xheight)
        basic_ctx.line_to(self.z_squarebuf_offset+self.z_width, self.z_4xheight+self.z_halfheight)
        basic_ctx.line_to(self.z_squarebuf_offset+self.z_halfwidth, self.z_5xheight)
        basic_ctx.close_path()
        basic_ctx.fill()

        # Draw the squares
        for y in range(len(self.map.squares)):
            huge_gfxes = []
            for x in range(len(self.map.squares[y])):
                self.draw_square(x, y)
                if self.map.squares[y][x].scriptid == 21:
                    huge_gfxes.append(self.map.squares[y][x])
            if self.req_book == 2 and self.huge_gfx_toggle.get_active():
                for square in huge_gfxes:
                    self.draw_huge_gfx(square)
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
