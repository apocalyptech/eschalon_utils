#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2014 CJ Kucera, Elliot Kendall
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

from eschalon.constants import constants as c
from eschalon.item import Item
from eschalon.savefile import LoadException


class Merchant(object):
    """
    Class to hold information about a merchant file (*.mer).
    I'm not sure if this'll ever actually get integrated into
    anything, but sometimes you just don't want to wait for
    a merchant to reset, y'know?

    This has only been tested on Book III files.  I assume that
    probably it'd work fine on others (at least Book II), but
    YMMV.
    """

    def __init__(self):
        """ Create a new object """

        # Known fields
        self.items = []
        self.day_stocked = 0
        self.gold = 0

    def item_count(self):
        """ How many items we have. """
        return len(self.items)

    def read(self, df):
        """ Read our data. """

        df.open_r()
        self.day_stocked = df.readint()
        item_count = df.readint()
        self.gold = df.readint()

        for i in range(item_count):
            item = Item.new(c.book)
            item.read(df)
            self.items.append(item)

        extradata = df.read()
        if len(extradata) > 0:
            raise LoadException('Extra data at end of merchant file')

        df.close()

    def write(self, df):
        """ Write to a file. """

        df.open_w()
        df.writeint(self.day_stocked)
        df.writeint(self.item_count())
        df.writeint(self.gold)
        for item in self.items:
            item.write(df)
        df.close()

    def reset(self, turn_number):
        """
        Given a turn number, reset the day_stocked field so that the
        merchant will regenerate their stock.  We could probably just
        globally set this to zero, but instead we'll be more clever
        about it.
        """
        cur_day = turn_number / (60 * 24)
        last_week -= 7
        if last_week < 0:
            last_week = 0
        self.day_stocked = last_week
