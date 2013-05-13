#!/usr/bin/env python

import gtk
from eschalon.maingui import MainGUI
from eschalon.mapgui import MapGUI
from eschalon.preferences import Prefs

class EschalonUtils:
    options = {
            'gui': True,
            'list': False,
            'listoptions' : {
                'all': False,
                'squares': False,
                'objects': False,
                'txtmap': False
                },
            'unknowns': False,
            'filename' : None
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

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_border_width(10)
        window.connect("delete_event", self.delete_event)
        window.connect("destroy", self.destroy)

        col = gtk.VBox(homogeneous=False, spacing=10)
        col.show()
        window.add(col)

        row1 = gtk.HBox(homogeneous=False, spacing=10)
        row2 = gtk.HBox(homogeneous=False, spacing=10)
        for row in [gtk.Label('Select a utility to run'), row1, row2]:
            row.show()
            col.add(row)
 
        buttons = { "Book I Character Editor": [self.b1char, row1],
                    "Book I Map Editor": [self.b1map, row1],
                    "Book II Character Editor": [self.b2char, row2],
                    "Book II Map Editor": [self.b2map, row2]}
        for label in buttons.keys():
            button = gtk.Button(label)
            button.connect_object("clicked", gtk.Widget.hide, window)
            button.connect("clicked", buttons[label][0], None)
            button.connect_object("clicked", gtk.Widget.destroy, window)
            button.show()
            buttons[label][1].add(button)

        window.show()

    def main(self):
        gtk.main()

eutils = EschalonUtils()
eutils.main()
