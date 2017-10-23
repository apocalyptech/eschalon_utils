#!/usr/bin/env python2

import os
import sys
from typing import Callable
from gi import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')
from gi.repository import Gtk
from eschalon import version
from eschalon.maingui import MainGUI
from eschalon.mapgui import MapGUI
from eschalon.preferences import Prefs


class BookChooser(object):
    def char(self, book_id: object) -> Callable[object]:
        def launcher(widget):
            prog = MainGUI(None, Prefs(), book_id)
            return prog.run()
        return launcher

    def map(self, book_id):
        def launcher(widget):
            prog = MapGUI(None, Prefs(), book_id)
            return prog.run()
        return launcher

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        Gtk.main_quit()

    def add_launchers(self, book, char_launcher, map_launcher):
        """
        Adds a set of launchers to our table.
        """

        # First the label
        label = Gtk.Label()
        label.set_markup('<b>Book %s Utilities:</b>' % book)
        align = Gtk.Alignment.new(0, 0, 0, 1)
        align.set_padding(5, 5, 5, 5)
        align.add(label)
        self.table.attach(align, 0, 2, self.cur_row, self.cur_row + 1,
                          Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 5)
        self.cur_row += 1

        # Now the character buttons
        button = Gtk.Button('Book %s Character Editor' % book)
        button.connect_object("clicked", Gtk.Widget.hide, self.window)
        button.connect("clicked", char_launcher)
        button.connect_object("clicked", Gtk.Widget.destroy, self.window)
        align = Gtk.Alignment.new(0, 0, 1, 1)
        align.set_padding(0, 10, 20, 5)
        align.add(button)
        self.table.attach(align, 0, 1, self.cur_row, self.cur_row + 1,
                          Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 5)

        # Map button
        button = Gtk.Button('Book %s Map Editor' % book)
        button.connect_object("clicked", Gtk.Widget.hide, self.window)
        button.connect("clicked", map_launcher)
        button.connect_object("clicked", Gtk.Widget.destroy, self.window)
        align = Gtk.Alignment.new(0, 0, 1, 1)
        align.set_padding(0, 10, 5, 5)
        align.add(button)
        self.table.attach(align, 1, 2, self.cur_row, self.cur_row + 1,
                          Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 5)

        self.cur_row += 1

    def __init__(self):
        """
        Set up our window
        """
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_border_width(10)
        self.window.set_title('Eschalon Map/Character Editor v%s' % version)
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)

        col = Gtk.VBox(homogeneous=False, spacing=10)
        self.window.add(col)

        # First our header.  We're duplicating some code from basegui with the path
        # detection, but having an icon makes the dialog look less sparse
        label = Gtk.Label()
        label.set_markup(
            '<big><b>Eschalon Map/Character Editor v%s</b></big>' % version)
        hbox = Gtk.HBox()
        if getattr(sys, 'frozen', False):
            icon_filename = os.path.join(os.path.dirname(
                sys.executable), 'data', 'eb1_icon_64.png')
        else:
            icon_filename = os.path.join(os.path.dirname(
                __file__), 'data', 'eb1_icon_64.png')
        hbox.pack_start(Gtk.image_new_from_file(icon_filename), False, False)
        hbox.pack_start(label, False, False)
        align = Gtk.Alignment.new(0, 0, 1, 1)
        align.set_padding(5, 5, 40, 40)
        align.add(hbox)
        col.add(align)

        # Now our table of buttons
        self.table = Gtk.Table(6, 2)
        self.cur_row = 0
        for i in range(1, 4):
            self.add_launchers('I' * i, self.char(i), self.map(i))
        col.add(self.table)

        # Close button at the bottom
        bbox = Gtk.HButtonBox()
        button = Gtk.Button(stock=Gtk.STOCK_CLOSE)
        button.connect_object("clicked", Gtk.Widget.hide, self.window)
        button.connect_object("clicked", Gtk.Widget.destroy, self.window)
        bbox.add(button)
        align = Gtk.Alignment.new(1, 0, 0, 1)
        align.set_padding(5, 5, 5, 5)
        align.add(bbox)
        col.add(align)

        # Show everything
        self.window.show_all()

    def run(self) -> object:
        Gtk.main()
