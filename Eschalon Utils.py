#!/usr/bin/env python2

import os
import sys
import gtk
from eschalon import version
from eschalon.maingui import MainGUI
from eschalon.mapgui import MapGUI
from eschalon.preferences import Prefs


class EschalonUtils:
    options = {
        'gui': True,
        'list': False,
        'listoptions': {
            'all': False,
            'tiles': False,
            'objects': False,
            'txtmap': False
        },
        'unknowns': False,
        'filename': None
    }

    def b1char(self, widget, data=None):
        prog = MainGUI(self.options, Prefs(), 1)
        return prog.run()

    def b1map(self, widget, data=None):
        prog = MapGUI(self.options, Prefs(), 1)
        return prog.run()

    def b2char(self, widget, data=None):
        prog = MainGUI(self.options, Prefs(), 2)
        return prog.run()

    def b2map(self, widget, data=None):
        prog = MapGUI(self.options, Prefs(), 2)
        return prog.run()

    def b3char(self, widget, data=None):
        prog = MainGUI(self.options, Prefs(), 3)
        return prog.run()

    def b3map(self, widget, data=None):
        prog = MapGUI(self.options, Prefs(), 3)
        return prog.run()

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def add_launchers(self, book, char_launcher, map_launcher):
        """
        Adds a set of launchers to our table.
        """

        # First the label
        label = gtk.Label()
        label.set_markup('<b>Book %s Utilities:</b>' % (book))
        align = gtk.Alignment(0, 0, 0, 1)
        align.set_padding(5, 5, 5, 5)
        align.add(label)
        self.table.attach(align, 0, 2, self.cur_row, self.cur_row + 1,
                          gtk.EXPAND | gtk.FILL, 0, 5)
        self.cur_row += 1

        # Now the character buttons
        button = gtk.Button('Book %s Character Editor' % (book))
        button.connect_object("clicked", gtk.Widget.hide, self.window)
        button.connect("clicked", char_launcher, None)
        button.connect_object("clicked", gtk.Widget.destroy, self.window)
        align = gtk.Alignment(0, 0, 1, 1)
        align.set_padding(0, 10, 20, 5)
        align.add(button)
        self.table.attach(align, 0, 1, self.cur_row, self.cur_row + 1,
                          gtk.EXPAND | gtk.FILL, 0, 5)

        # Map button
        button = gtk.Button('Book %s Map Editor' % (book))
        button.connect_object("clicked", gtk.Widget.hide, self.window)
        button.connect("clicked", map_launcher, None)
        button.connect_object("clicked", gtk.Widget.destroy, self.window)
        align = gtk.Alignment(0, 0, 1, 1)
        align.set_padding(0, 10, 5, 5)
        align.add(button)
        self.table.attach(align, 1, 2, self.cur_row, self.cur_row + 1,
                          gtk.EXPAND | gtk.FILL, 0, 5)

        self.cur_row += 1

    def __init__(self):
        """
        Set up our window
        """
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_border_width(10)
        self.window.set_title('Eschalon Map/Character Editor v%s' % (version))
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)

        col = gtk.VBox(homogeneous=False, spacing=10)
        self.window.add(col)

        # First our header.  We're duplicating some code from basegui with the path
        # detection, but having an icon makes the dialog look less sparse
        label = gtk.Label()
        label.set_markup(
            '<big><b>Eschalon Map/Character Editor v%s</b></big>' % (version))
        hbox = gtk.HBox()
        if getattr(sys, 'frozen', False):
            icon_filename = os.path.join(os.path.dirname(
                sys.executable), 'data', 'eb1_icon_64.png')
        else:
            icon_filename = os.path.join(os.path.dirname(
                __file__), 'data', 'eb1_icon_64.png')
        hbox.pack_start(gtk.image_new_from_file(icon_filename), False, False)
        hbox.pack_start(label, False, False)
        align = gtk.Alignment(0, 0, 1, 1)
        align.set_padding(5, 5, 40, 40)
        align.add(hbox)
        col.add(align)

        # Now our table of buttons
        self.table = gtk.Table(6, 2)
        self.cur_row = 0
        self.add_launchers('I', self.b1char, self.b1map)
        self.add_launchers('II', self.b2char, self.b2map)
        self.add_launchers('III', self.b3char, self.b3map)
        col.add(self.table)

        # Close button at the bottom
        bbox = gtk.HButtonBox()
        button = gtk.Button(stock=gtk.STOCK_CLOSE)
        button.connect_object("clicked", gtk.Widget.hide, self.window)
        button.connect_object("clicked", gtk.Widget.destroy, self.window)
        bbox.add(button)
        align = gtk.Alignment(1, 0, 0, 1)
        align.set_padding(5, 5, 5, 5)
        align.add(bbox)
        col.add(align)

        # Show everything
        self.window.show_all()

    def main(self):
        gtk.main()


if __name__ == '__main__':
    eutils = EschalonUtils()
    eutils.main()
