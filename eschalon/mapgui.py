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
from eschalonb1 import app_name, version, url, authors

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

        # Graphics we'll need
        self.gfx = Gfx()

        # Start up our GUI
        self.gladefile = os.path.join(os.path.dirname(__file__), 'mapgui.glade')
        self.wTree = gtk.glade.XML(self.gladefile)
        self.window = self.get_widget('mainwindow')
        self.infowindow = self.get_widget('infowindow')
        self.maparea = self.get_widget('maparea')
        self.mapname_label = self.get_widget('mapname')
        self.coords_label = self.get_widget('coords')
        self.mainscroll = self.get_widget('mainscroll')
        self.zoom_in_button = self.get_widget('zoom_in_button')
        self.zoom_out_button = self.get_widget('zoom_out_button')
        self.floor_toggle = self.get_widget('floor_button')
        self.decal_toggle = self.get_widget('decal_button')
        self.object_toggle = self.get_widget('object_button')
        self.objectdecal_toggle = self.get_widget('objectdecal_button')
        self.barrier_toggle = self.get_widget('barrier_button')
        self.script_toggle = self.get_widget('script_button')
        self.entity_toggle = self.get_widget('entity_button')
        self.info_button = self.get_widget('info_button')
        self.infotext = self.get_widget('infotext')
        self.infobuffer = gtk.TextBuffer()
        self.infotext.set_buffer(self.infobuffer)
        self.infoscroll = self.get_widget('infoscroll')
        if (self.window):
            self.window.connect('destroy', gtk.main_quit)

        # Preferences window
        self.prefs_init()

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

        # Load in our mouse map (to determine which square we're pointing at)
        self.mousemap = {}
        for zoom in self.zoom_levels:
            self.mousemap[zoom] = gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(__file__), 'iso_mousemap_%d.png' % (zoom))).get_pixels_array()

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

    def set_zoom_vars(self, width):
        """ Set a bunch of parameters we use to draw, based on how wide our squares should be. """
        self.curzoom = width
        self.z_width = width
        self.z_height = int(self.z_width/2)
        self.z_halfwidth = self.z_height
        self.z_halfheight = int(self.z_height/2)
        self.z_mapsize_x = self.z_width*101
        self.z_mapsize_y = int(self.z_mapsize_x/2)
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
            if (self.sq_x_prev != -1):
                self.cleansquares.append((self.sq_x_prev, self.sq_y_prev))
            self.cleansquares.append((self.sq_x, self.sq_y))
            self.sq_x_prev = self.sq_x
            self.sq_y_prev = self.sq_y
        self.coords_label.set_markup('<i>(%d, %d)</i>' % (self.sq_x, self.sq_y))

        # Now queue up a draw
        self.maparea.queue_draw()

    def on_clicked(self, widget, event):
        """ Handle a mouse click. """

        if (self.sq_y < len(self.map.squares)):
            if (self.sq_x < len(self.map.squares[self.sq_y])):
                self.infobuffer.insert(self.infobuffer.get_end_iter(), "Square at (%d, %d):\n%s\n" % (self.sq_x, self.sq_y, self.map.squares[self.sq_y][self.sq_x].display(True)))
                adjust = self.infoscroll.get_vadjustment()
                adjust.set_value(adjust.upper)
                if (not self.info_button.get_active()):
                    self.info_button.clicked()
                self.infowindow.show()
                #print "Square at %d x %d - " % (self.sq_x, self.sq_y)
                #self.map.squares[self.sq_y][self.sq_x].display(True)

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

    def draw_square(self, x, y):
        """ Draw a single square of the map. """

        # TODO: Layers are pretty inefficient here, and regardless there's currently lots
        # of graphical glitches when you move the mouse around.  That needs to get fixed.
        barrier = False
        script = False
        clear = False
        pointer = False
        entity = False

        if (x == self.sq_x and y == self.sq_y):
            pointer = True
            color = self.gc_red
        elif (self.map.squares[y][x].entity is not None):
            entity = True
            if (self.map.squares[y][x].entity.friendly == 1):
                color = self.gc_yellow
            else:
                color = self.gc_red
        elif (self.map.squares[y][x].scriptid != 0 and len(self.map.squares[y][x].scripts) > 0):
            script = True
            color = self.gc_green
        elif (self.map.squares[y][x].scriptid != 0 and len(self.map.squares[y][x].scripts) == 0):
            script = True
            color = self.gc_cyan
        elif (self.map.squares[y][x].scriptid == 0 and len(self.map.squares[y][x].scripts) > 0):
            # afaik, this doesn't happen.  should use something other than red here, though
            script = True
            color = self.gc_red
        elif (self.map.squares[y][x].wall == 1):
            barrier = True
            color = self.gc_white
        elif (self.map.squares[y][x].floorimg == 126):
            barrier = True
            color = self.gc_blue
        else:
            clear = True
            color = self.gc_black

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
        x2 = xstart+self.z_halfwidth
        x3 = xstart+self.z_width-1
        x4 = x2

        ystart = y*self.z_halfheight
        y1 = ystart+self.z_halfheight
        y2 = ystart+1
        y3 = y1
        y4 = ystart+self.z_height-1
        if (y4-y2<3):
            # This is for our two most-zoomed-out levels
            y4 = y4 + 1
            y2 = y2 - 1

        # Let's just go ahead and do this *always*
        self.pixmap.draw_polygon(self.gc_black, True, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

        # Draw the floor tile
        if (not pointer and self.floor_toggle.get_active()):
            pixbuf = self.gfx.get_floor(self.map.squares[y][x].floorimg, self.curzoom)
            if (pixbuf is not None):
                self.pixmap.draw_pixbuf(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, x1, y2)

        # Draw the floor decal
        if (not pointer and self.decal_toggle.get_active()):
            pixbuf = self.gfx.get_decal(self.map.squares[y][x].decalimg, self.curzoom)
            if (pixbuf is not None):
                self.pixmap.draw_pixbuf(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, x1, y2)

        # Draw the object
        if (not pointer and self.object_toggle.get_active()):
            (pixbuf, pixheight) = self.gfx.get_object(self.map.squares[y][x].wallimg, self.curzoom)
            if (pixbuf is not None):
                self.pixmap.draw_pixbuf(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, x1, y2-(self.z_height*pixheight))

        # Draw the object decal
        if (not pointer and self.objectdecal_toggle.get_active()):
            pixbuf = self.gfx.get_object_decal(self.map.squares[y][x].walldecalimg, self.curzoom)
            if (pixbuf is not None):
                self.pixmap.draw_pixbuf(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, x1, y2-self.z_width)

        # Draw Barriers
        if (barrier and self.barrier_toggle.get_active()):
            self.pixmap.draw_polygon(color, True, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

        # Draw Scripts
        if (script and self.script_toggle.get_active()):
            self.pixmap.draw_polygon(color, True, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

        # Draw Entities
        if (entity and self.entity_toggle.get_active()):
            self.pixmap.draw_polygon(color, True, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

        # Finally, draw the mouse pointer
        if (pointer):
            self.pixmap.draw_polygon(color, True, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])

    def expose_map(self, widget, event):
        # TODO: Would like most of this to happen in draw_map instead (getting rid of the self.mapinit check)
        # This may be the only way when doing startup though...  self.maparea.window isn't useful until we're in
        # the expose event, apparently.  At least when loading the initial map.

        # Now do our work
        if (self.mapinit):
            for (x, y) in self.cleansquares:
                self.draw_square(x, y)
        else:
            self.maparea.set_size_request(self.z_mapsize_x, self.z_mapsize_y)
            self.pixmap = gtk.gdk.Pixmap(self.maparea.window, self.z_mapsize_x, self.z_mapsize_y)
            self.gc_red = gtk.gdk.GC(self.maparea.window)
            self.gc_red.set_rgb_fg_color(gtk.gdk.Color(65535, 0, 0))
            self.gc_green = gtk.gdk.GC(self.maparea.window)
            self.gc_green.set_rgb_fg_color(gtk.gdk.Color(0, 65535, 0))
            self.gc_yellow = gtk.gdk.GC(self.maparea.window)
            self.gc_yellow.set_rgb_fg_color(gtk.gdk.Color(65535, 65535, 0))
            self.gc_cyan = gtk.gdk.GC(self.maparea.window)
            self.gc_cyan.set_rgb_fg_color(gtk.gdk.Color(0, 65535, 65535))
            self.gc_blue = gtk.gdk.GC(self.maparea.window)
            self.gc_blue.set_rgb_fg_color(gtk.gdk.Color(0, 0, 65535))
            self.gc_white = gtk.gdk.GC(self.maparea.window)
            self.gc_white.set_rgb_fg_color(gtk.gdk.Color(65535, 65535, 65535))
            self.gc_black = gtk.gdk.GC(self.maparea.window)
            self.gc_black.set_rgb_fg_color(gtk.gdk.Color(0, 0, 0))
            self.pixmap.draw_rectangle(self.gc_black, True, 0, 0, self.z_mapsize_x, self.z_mapsize_y)
            for y in range(len(self.map.squares)):
                for x in range(len(self.map.squares[y])):
                    self.draw_square(x, y)
            self.mapinit = True

        # Make sure our to-clean list is empty
        self.cleansquares = []

        # This is about all we should *actually* need in here
        self.maparea.window.draw_drawable(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], self.pixmap, 0, 0, 0, 0, self.z_mapsize_x, self.z_mapsize_y)

