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
from eschalonb1.square import Square
from eschalonb1.basegui import BaseGUI
from eschalonb1.mapscript import Mapscript
from eschalonb1.savefile import LoadException
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
        self.window = self.get_widget('mainwindow')
        self.infowindow = self.get_widget('infowindow')
        self.squarewindow = self.get_widget('squarewindow')
        self.maparea = self.get_widget('maparea')
        self.mapname_label = self.get_widget('mapname')
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
        self.barrier_toggle = self.get_widget('barrier_button')
        self.script_toggle = self.get_widget('script_button')
        self.entity_toggle = self.get_widget('entity_button')
        self.info_button = self.get_widget('info_button')
        self.infotext = self.get_widget('infotext')
        self.infobuffer = gtk.TextBuffer()
        self.infotext.set_buffer(self.infobuffer)
        self.infoscroll = self.get_widget('infoscroll')
        self.composite_area = self.get_widget('composite_area')
        if (self.window):
            self.window.connect('destroy', gtk.main_quit)

        # Preferences window - also load in our graphics
        self.prefs_init(self.prefs)
        if (not self.require_gfx()):
            return
        self.gfx = Gfx(self.prefs)

        # Dictionary of signals.
        dic = { 'gtk_main_quit': self.gtk_main_quit,
                'on_load': self.on_load,
                'on_about': self.on_about,
                'on_clicked': self.on_clicked,
                'zoom_in': self.zoom_in,
                'zoom_out': self.zoom_out,
                'on_mouse_changed': self.on_mouse_changed,
                'expose_map': self.expose_map,
                'realize_map': self.realize_map,
                'map_toggle': self.map_toggle,
                'info_toggle': self.info_toggle,
                'infowindow_clear': self.infowindow_clear,
                'on_entid_changed': self.on_entid_changed,
                'on_singleval_square_changed_int': self.on_singleval_square_changed_int,
                'on_singleval_ent_changed_int': self.on_singleval_ent_changed_int,
                'on_singleval_ent_changed_str': self.on_singleval_ent_changed_str,
                'on_entity_toggle': self.on_entity_toggle,
                'on_floor_changed': self.on_floor_changed,
                'on_decal_changed': self.on_decal_changed,
                'on_wall_changed': self.on_wall_changed,
                'on_walldecal_changed': self.on_walldecal_changed,
                'on_squarewindow_close': self.on_squarewindow_close,
                'on_prefs': self.on_prefs
                }
        self.wTree.signal_autoconnect(dic)

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

        # Blank pixbuf to use in the square editing window
        self.comp_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 52, 130)

        # Load in our mouse map (to determine which square we're pointing at)
        self.mousemap = {}
        for zoom in self.zoom_levels:
            self.mousemap[zoom] = gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(__file__), 'iso_mousemap_%d.png' % (zoom))).get_pixels_array()

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
            table[item] = key
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

        # Now show our window
        self.window.show()
        gtk.main()

    def putstatus(self, text):
        """ Pushes a message to the status bar """
        self.statusbar.push(self.sbcontext, text)

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
        self.origmap = map
        self.map = map.replicate()

        # Update our status bar
        self.putstatus('Editing ' + self.map.df.filename)

        # Update the map title
        self.mapname_label.set_text(self.map.mapname)

        # Load information from the character
        #self.populate_form_from_char()
        self.mapinit = False
        self.draw_map()

        # Return success
        return True

    def gtk_main_quit(self, widget=None):
        """ Main quit function. """
        #if (self.has_unsaved_changes()):
        #    quitconfirm = self.get_widget('quitwindow')
        #    response = quitconfirm.run()
        #    quitconfirm.hide()
        #    if (response == gtk.RESPONSE_OK):
        #        gtk.main_quit()
        #else:
        #    gtk.main_quit()
        gtk.main_quit()

    # Show the About dialog
    def on_about(self, widget):
        global app_name, version, url, authors

        about = self.get_widget('aboutwindow')

        # If the object doesn't exist in our cache, create it
        if (about == None):
            about = gtk.AboutDialog()
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

    def on_entid_changed(self, widget):
        idx = widget.get_active()
        name = self.entitykeys[idx]
        entid = self.entityrev[name]
        self.map.squares[self.sq_y][self.sq_x].entity.entid = entid

    def on_dropdownplusone_ent_changed(self, widget):
        wname = widget.get_name()
        ent = self.map.squares[self.sq_y][self.sq_x].entity
        ent.__dict__[wname] = widget.get_active() + 1

    def on_singleval_ent_changed_int(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        ent = self.map.squares[self.sq_y][self.sq_x].entity
        ent.__dict__[wname] = widget.get_value()

    def on_singleval_ent_changed_str(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        ent = self.map.squares[self.sq_y][self.sq_x].entity
        ent.__dict__[wname] = widget.get_text()

    def on_singleval_square_changed_int(self, widget):
        """ Update the appropriate bit in memory. """
        wname = widget.get_name()
        square = self.map.squares[self.sq_y][self.sq_x]
        square.__dict__[wname] = widget.get_value()

    def on_floor_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        pixbuf = self.gfx.get_floor(widget.get_value(), None, True)
        if (pixbuf is None):
            self.get_widget('floorimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('floorimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_decal_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        pixbuf = self.gfx.get_decal(widget.get_value(), None, True)
        if (pixbuf is None):
            self.get_widget('decalimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('decalimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_wall_changed(self, widget):
        """ Update the appropriate image when necessary. """
        self.on_singleval_square_changed_int(widget)
        (pixbuf, height) = self.gfx.get_object(widget.get_value(), None, True)
        if (pixbuf is None):
            self.get_widget('wallimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('wallimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_walldecal_changed(self, widget):
        self.on_singleval_square_changed_int(widget)
        """ Update the appropriate image when necessary. """
        pixbuf = self.gfx.get_object_decal(widget.get_value(), None, True)
        if (pixbuf is None):
            self.get_widget('walldecalimg_image').set_from_stock(gtk.STOCK_EDIT, 2)
        else:
            self.get_widget('walldecalimg_image').set_from_pixbuf(pixbuf)
        self.update_composite()

    def on_squarewindow_close(self, widget):
        """
        Closes the square-editing window.  Our primary goal here is to redraw the
        square that was just edited.  Because we don't really keep composite caches
        around (should we?) this entails drawing all the squares behind the square we
        just edited, the square itself, and then four more "levels" of squares below, as
        well, because objects may be obscuring the one we just edited.  Because of the
        isometric presentation, this means that we'll be redrawing 29 total squares.

        Note that we could cut down on that number by doing some logic - ie: we really
        would only have to draw the bottom-most square if it contained the tallest tree
        graphic, and there's no need to draw the floor or floor decals on any tile below
        the one we just edited.  Still, because this is a user-initiated action, I don't
        think it's really worth it to optimize that out.  I don't think the extra processing
        will be noticeable.

        Also note that none of that is actually necessary if the user didn't actually change
        anything.  Whatever.
        """

        # Figure out our dimensions
        mid_x = self.sq_x
        mid_y = self.sq_y - 8
        corner_y = self.sq_y - 1 - 8
        global_x = self.sq_x * self.z_width
        if ((self.sq_y % 2) == 0):
            left_x = self.sq_x - 1
            rt_x = self.sq_x
        else:
            left_x = self.sq_x
            rt_x = self.sq_x + 1
            global_x = global_x + self.z_halfwidth

        # Set up a surface to use
        over_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_width, self.z_5xheight)
        over_ctx = cairo.Context(over_surf)
        over_ctx.set_source_rgba(0, 0, 0, 1)
        over_ctx.paint()

        # Grab some local vars
        sq_buf = self.squarebuf
        sq_ctx = self.squarebuf_ctx
        squares = self.map.squares

        # Loop through and composite the new image area
        for i in range(10):
            # Draw corners first, then mid
            if (corner_y > -1 and corner_y < 200):
                yval = self.z_halfheight+((i-5)*self.z_height)
                if (left_x > -1 and left_x < 100):
                    self.draw_square(left_x, corner_y, False, False)
                    over_ctx.set_source_surface(sq_buf, -self.z_halfwidth, yval)
                    over_ctx.paint()
                if (rt_x > -1 and rt_x < 100):
                    self.draw_square(rt_x, corner_y, False, False)
                    over_ctx.set_source_surface(sq_buf, self.z_halfwidth, yval)
                    over_ctx.paint()
            if (i < 9):
                if (mid_y > -1 and mid_y < 200 and mid_x > -1 and mid_x < 100):
                    self.draw_square(mid_x, mid_y, False, False)
                    over_ctx.set_source_surface(sq_buf, 0, (i-4)*self.z_height)
                    over_ctx.paint()
            corner_y = corner_y + 2
            mid_y = mid_y + 2

        # Now superimpose that onto our main map image
        self.guicache_ctx.set_source_surface(over_surf, global_x+1, self.z_halfheight*(self.sq_y-8)+1)
        self.guicache_ctx.paint()
        self.ctx.set_source_surface(over_surf, global_x+1, self.z_halfheight*(self.sq_y-8)+1)
        self.ctx.paint()
        self.cleansquares.append((self.sq_x, self.sq_y))
        self.maparea.queue_draw()

        # Finally, close out the window
        self.squarewindow.hide()

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
        self.mapinit = False

        # TODO: Should queue a redraw here, probably...

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

    def on_entity_toggle(self, widget, event):
        pass

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
            if (square.entity.entid in entitytable):
                if (entitytable[square.entity.entid] in self.entitykeys):
                    idx = self.entitykeys.index(entitytable[square.entity.entid])
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

    def on_clicked(self, widget, event):
        """ Handle a mouse click. """

        if (self.sq_y < len(self.map.squares)):
            if (self.sq_x < len(self.map.squares[self.sq_y])):
                self.populate_squarewindow_from_square(self.map.squares[self.sq_y][self.sq_x])
                self.get_widget('squarelabel').set_markup('<b>Map Square (%d, %d)</b>' % (self.sq_x, self.sq_y))
                self.squarewindow.show()
                #self.infobuffer.insert(self.infobuffer.get_end_iter(), "Square at (%d, %d):\n%s\n" % (self.sq_x, self.sq_y, self.map.squares[self.sq_y][self.sq_x].display(True)))
                #adjust = self.infoscroll.get_vadjustment()
                #adjust.set_value(adjust.upper)
                #if (not self.info_button.get_active()):
                #    self.info_button.clicked()
                #self.infowindow.show()
                ##print "Square at %d x %d - " % (self.sq_x, self.sq_y)
                ##self.map.squares[self.sq_y][self.sq_x].display(True)

    def info_toggle(self, widget):
        if (self.info_button.get_active()):
            self.infowindow.show()
        else:
            self.infowindow.hide()

    def infowindow_clear(self, widget):
        self.infobuffer.set_text('')

    def map_toggle(self, widget):
        self.mapinit = False
        self.draw_map()

    def draw_map(self):
        #self.frame = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 800, 800)
        if (self.maparea.get_style().black_gc is not None):
            self.expose_map(None, None)

    def realize_map(self, event):
        pass

    # Assumes that the context is squarebuf_ctx, hence the hardcoded width/height
    # We're passing it in so we're not constantly referencing self.squarebuf_ctx
    def composite_simple(self, context, color):
        context.save()
        context.set_operator(cairo.OPERATOR_ATOP)
        context.set_source_rgba(*color)
        context.rectangle(0, 0, self.z_width, self.z_5xheight)
        context.fill()
        context.restore()

    def draw_square(self, x, y, usecache=False, do_main_paint=True):
        """ Draw a single square of the map. """

        # TODO: Layers are pretty inefficient and slow here
        barrier = False
        script = False
        clear = False
        pointer = False
        entity = False

        # Use local vars instead of continually calling out
        square = self.map.squares[y][x]
        sq_ctx = self.squarebuf_ctx
        main_ctx = self.ctx

        if (do_main_paint and x == self.sq_x and y == self.sq_y):
            pointer = (1, 1, 1, 0.5)
        elif (square.entity is not None):
            entity = True
            if (square.entity.friendly == 1):
                entity = (1, 1, 0, 0.5)
            else:
                entity = (1, 0, 0, 0.5)
        elif (square.scriptid != 0 and len(square.scripts) > 0):
            script = (0, 1, 0, 0.5)
        elif (square.scriptid != 0 and len(square.scripts) == 0):
            script = (0, .784, .784, 0.5)
        elif (square.scriptid == 0 and len(square.scripts) > 0):
            # afaik, this doesn't happen.  should use something other than red here, though
            script = (1, 0, 0, 0.5)
        elif (square.wall == 1):
            barrier = (.784, .784, .784, 0.5)
        elif (square.floorimg == 126):
            barrier = (0, 0, .784, 0.5)
        else:
            clear = True

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
        sq_ctx.set_source_surface(self.blanksquare)
        sq_ctx.paint()
        sq_ctx.restore()

        # Draw the floor tile
        if (self.floor_toggle.get_active()):
            pixbuf = self.gfx.get_floor(square.floorimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_4xheight)
                sq_ctx.paint()

        # Draw the floor decal
        if (self.decal_toggle.get_active()):
            pixbuf = self.gfx.get_decal(square.decalimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_4xheight)
                sq_ctx.paint()

        # Draw the object
        wallid = square.wallimg
        if (self.object_toggle.get_active() and wallid<161):
            (pixbuf, pixheight) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_height*(4-pixheight))
                sq_ctx.paint()

        # Draw walls
        if (self.wall_toggle.get_active() and wallid<251 and wallid>160):
            (pixbuf, pixheight) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_height*(4-pixheight))
                sq_ctx.paint()

        # Draw trees
        if (self.tree_toggle.get_active() and wallid>250):
            (pixbuf, pixheight) = self.gfx.get_object(wallid, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_height*(4-pixheight))
                sq_ctx.paint()

        # Draw the object decal
        if (self.objectdecal_toggle.get_active()):
            pixbuf = self.gfx.get_object_decal(square.walldecalimg, self.curzoom)
            if (pixbuf is not None):
                sq_ctx.set_source_surface(pixbuf, 0, self.z_2xheight)
                sq_ctx.paint()

        # Draw Barriers
        # TODO: Drawing barriers on water is pretty lame; don't do that.
        # (perhaps unless asked to)
        if (barrier and self.barrier_toggle.get_active()):
            self.composite_simple(sq_ctx, barrier)

        # Draw Scripts
        if (script and self.script_toggle.get_active()):
            self.composite_simple(sq_ctx, script)

        # Draw Entities
        if (entity and self.entity_toggle.get_active()):
            self.composite_simple(sq_ctx, entity)

        # Now draw the pixbuf onto our pixmap
        if (do_main_paint):
            if (usecache):
                # We only get here when we're the pointer
                self.composite_simple(sq_ctx, pointer)
                main_ctx.set_source_surface(self.squarebuf, x1, top-buftop)
                main_ctx.paint()
            else:
                # This is only for the initial map population
                self.guicache_ctx.set_source_surface(self.squarebuf, x1, top-buftop)
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

    def expose_map(self, widget, event):
        # TODO: Would like most of this to happen in draw_map instead (getting rid of the self.mapinit check)
        # This may be the only way when doing startup though...  self.maparea.window isn't useful until we're in
        # the expose event, apparently.  At least when loading the initial map.

        # Now do our work
        if (self.mapinit):
            for (x, y) in self.cleansquares:
                self.draw_square(x, y, True)
        else:
            time_a = time.time()
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

            # Set up a "blank" tile to draw everything else on top of
            self.blanksquare = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.z_width, self.z_5xheight)
            sq_ctx = cairo.Context(self.blanksquare)
            sq_ctx.set_source_rgba(0, 0, 0, 1)
            sq_ctx.move_to(0, self.z_4xheight+self.z_halfheight)
            sq_ctx.line_to(self.z_halfwidth, self.z_4xheight)
            sq_ctx.line_to(self.z_width, self.z_4xheight+self.z_halfheight)
            sq_ctx.line_to(self.z_halfwidth, self.z_5xheight)
            sq_ctx.close_path()
            sq_ctx.fill()

            # Draw the squares
            time_c = time.time()
            for y in range(len(self.map.squares)):
                for x in range(len(self.map.squares[y])):
                    self.draw_square(x, y)
            time_d = time.time()

            # Finish drawing
            self.ctx.set_source_surface(self.guicache, 0, 0)
            self.ctx.paint()

            # ... and finish up, and report some timing information
            self.mapinit = True
            time_b = time.time()
            print "Map drawn in %d seconds, squares rendered in %d seconds" % (int(time_b-time_a), int(time_d-time_c))

        # Make sure our to-clean list is empty
        self.cleansquares = []

        # This is about all we should *actually* need in here
        # TODO: do we need this when doing Cairo?
        self.maparea.window.draw_drawable(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], self.pixmap, 0, 0, 0, 0, self.z_mapsize_x, self.z_mapsize_y)

