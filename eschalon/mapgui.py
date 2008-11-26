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

import sys
import os

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
from eschalonb1.exit import Exit
from eschalonb1.loadexception import LoadException
from eschalonb1 import app_name, version, url, authors

class MapGUI:

    def __init__(self, options):
        self.options = options

    def run(self):

        # We need this because Not Everything's in Glade anymore
        # Note that we have a couple of widget caches now, so those should
        # be consolidated
        self.fullwidgetcache = {}

        # Let's make sure our map object exists
        self.map = None

        self.mousex = -1
        self.mousey = -1

        # Start up our GUI
        self.gladefile = os.path.join(os.path.dirname(__file__), 'mapgui.glade')
        self.wTree = gtk.glade.XML(self.gladefile)
        self.window = self.get_widget('mainwindow')
        self.maparea = self.get_widget('maparea')
        if (self.window):
            self.window.connect('destroy', gtk.main_quit)

        # Dictionary of signals.
        dic = { 'gtk_main_quit': self.gtk_main_quit,
                'on_load': self.on_load,
                'on_about': self.on_about,
                'on_clicked': self.on_clicked,
                'on_mouse_changed': self.on_mouse_changed,
                'expose_map': self.expose_map,
                'realize_map': self.realize_map
                }
        self.wTree.signal_autoconnect(dic)

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
            # Don't know where to find most of these
            if 'win32' in sys.platform:
                pass
            elif 'cygwin' in sys.platform:
                pass
            elif 'darwin' in sys.platform:
                pass
            else:
                # This actually shouldn't be assumed at all
                path = '/usr/local/games/eschalon_book_1/data'
        else:
            path = os.path.dirname(self.map.df.filename)

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
                if (self.char == None):
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
            errordiag = self.get_widget('loaderrorwindow')
            errordiag.run()
            errordiag.hide()
            return False

        # Basic vars
        self.origmap = map
        self.map = map.replicate()

        # Update our status bar
        self.putstatus('Editing ' + self.map.df.filename)

        # Load information from the character
        #self.populate_form_from_char()
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

    def on_mouse_changed(self, widget, event):
        """ Keep track of where the mouse is """
        self.mousex = event.x
        self.mousey = event.y
        self.maparea.queue_draw()

    def on_clicked(self, widget, event):
        """ Handle a mouse click. """
        # TODO: This is duplicated in expose_map, and should be cleaned up, at any rate.
        squarewidth = 8
        squareheight = int(squarewidth/2)
        myx = int(self.mousex / squarewidth)
        myy = int(self.mousey / squareheight)

        if (myy < len(self.map.squares)):
            if (myx < len(self.map.squares[myy])):
                print "Square at %d x %d - " % (myx, myy)
                self.map.squares[myy][myx].display(True)
                print

    def draw_map(self):
        #self.frame = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 800, 800)
        if (self.maparea.get_style().black_gc is not None):
            self.expose_map(None, None)

    def realize_map(self, event):
        pass

    def expose_map(self, widget, event):
        # TODO: get this to happen in draw_map instead

        # How large are the squares?  (will zoom, later)
        squarewidth = 8

        # Other things we only want to calculate once
        halfwidth = int(squarewidth/2)
        squareheight = halfwidth
        halfheight = int(squareheight/2)
        mapsize = squarewidth*102

        # Check for mouse stuffs
        myx = int(self.mousex / squarewidth)
        myy = int(self.mousey / squareheight)

        # Now do our work
        self.maparea.set_size_request(mapsize, mapsize)
        style = self.maparea.get_style()
        pixmap = gtk.gdk.Pixmap(self.maparea.window, mapsize, mapsize)
        gc_red = gtk.gdk.GC(self.maparea.window)
        gc_red.set_rgb_fg_color(gtk.gdk.Color(65535, 0, 0))
        gc_green = gtk.gdk.GC(self.maparea.window)
        gc_green.set_rgb_fg_color(gtk.gdk.Color(0, 65535, 0))
        pixmap.draw_rectangle(style.black_gc, True, 0, 0, mapsize, mapsize)
        for y in range(len(self.map.squares)):
            if (y % 2 == 1):
                xpad = halfwidth
            else:
                xpad = 0
            for x in range(len(self.map.squares[y])):
                if (x == myx and y == myy):
                    color = gc_red
                elif (self.map.squares[y][x].unknown7 != 0):
                    color = gc_green
                else:
                    color = style.white_gc
                if (self.map.squares[y][x].wall == 1 or (x == myx and y == myy)):
                    x1 = (x*squarewidth)+xpad
                    y1 = (y*squareheight)+halfheight
                    x2 = (x*squarewidth)+halfwidth+xpad
                    y2 = y*squareheight
                    x3 = (x*squarewidth)+squarewidth+xpad
                    y3 = y1
                    x4 = x2
                    y4 = (y*squareheight)+squareheight
                    pixmap.draw_polygon(color, True, [(x1, y1), (x2, y2), (x3, y3), (x4, y4)])
        self.pixmap = pixmap

        # This is about all we should *actually* need in here
        self.maparea.window.draw_drawable(self.maparea.get_style().fg_gc[gtk.STATE_NORMAL], self.pixmap, 0, 0, 0, 0, mapsize, mapsize)

