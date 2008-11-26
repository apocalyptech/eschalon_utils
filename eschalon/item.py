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

from eschalonb1 import typetable, skilltable, attrtable, itemincrtable, flagstable

class Item:
    """Class to hold a single Item's information."""

    def __init__(self, zero=False):
        """ Create a new Item object with no information. """

        # Known fields
        self.type = -1
        self.subtype = -1
        self.item_name = ''
        self.weight = -1
        self.pictureid = -1
        self.value = -1
        self.canstack = -1
        self.quantity = -1
        self.basedamage = -1
        self.basearmor = -1
        self.attr_modified = -1
        self.attr_modifier = -1
        self.skill_modified = -1
        self.skill_modifier = -1
        self.hitpoint = -1
        self.mana = -1
        self.tohit = -1
        self.damage = -1
        self.armor = -1
        self.incr = -1
        self.flags = -1
        self.script = ''
        self.visibility = -1
        self.duration = -1

        # Unknown fields.
        self.zero1 = -1
        self.emptystr = ''

        # Now, after doing all that, zero things out if we were told to do so
        if (zero):
            self.tozero()

    def tozero(self):
        self.type = 0
        self.subtype = 0
        self.weight = 0
        self.pictureid = 0
        self.value = 0
        self.canstack = 0
        self.quantity = 0
        self.basedamage = 0
        self.basearmor = 0
        self.attr_modified = 0
        self.attr_modifier = 0
        self.skill_modified = 0
        self.skill_modifier = 0
        self.hitpoint = 0
        self.mana = 0
        self.tohit = 0
        self.damage = 0
        self.armor = 0
        self.incr = 0
        self.flags = 0
        self.visibility = 0
        self.duration = 0
        self.zero1 = 0
        self.item_name = ''
        self.script = ''
        self.emptystr = ''

    def replicate(self):
        newitem = Item()
        newitem.type = self.type
        newitem.subtype = self.subtype
        newitem.item_name = self.item_name
        newitem.weight = self.weight
        newitem.pictureid = self.pictureid
        newitem.value = self.value
        newitem.canstack = self.canstack
        newitem.quantity = self.quantity
        newitem.basedamage = self.basedamage
        newitem.basearmor = self.basearmor
        newitem.attr_modified = self.attr_modified
        newitem.attr_modifier = self.attr_modifier
        newitem.skill_modified = self.skill_modified
        newitem.skill_modifier = self.skill_modifier
        newitem.hitpoint = self.hitpoint
        newitem.mana = self.mana
        newitem.tohit = self.tohit
        newitem.damage = self.damage
        newitem.armor = self.armor
        newitem.incr = self.incr
        newitem.flags = self.flags
        newitem.script = self.script
        newitem.visibility = self.visibility
        newitem.duration = self.duration
        newitem.zero1 = self.zero1
        newitem.emptystr = self.emptystr
        return newitem

    def read(self, df):
        """ Given a file descriptor, read in the item. """

        self.type = df.readint()
        self.item_name = df.readstr()
        self.weight = df.readfloat()
        self.subtype = df.readint()
        self.visibility = df.readint()
        self.pictureid = df.readint()
        self.value = df.readint()
        self.canstack = df.readint()
        self.quantity = df.readint()
        self.basedamage = df.readint()
        self.basearmor = df.readint()
        self.attr_modified = df.readint()
        self.attr_modifier = df.readint()
        self.skill_modified = df.readint()
        self.skill_modifier = df.readint()
        self.hitpoint = df.readint()
        self.mana = df.readint()
        self.tohit = df.readint()
        self.damage = df.readint()
        self.armor = df.readint()
        self.incr = df.readint()
        self.flags = df.readint()
        self.script = df.readstr()
        self.emptystr = df.readstr()
        self.zero1 = df.readint()
        self.duration = df.readint()

    def write(self, df):
        """ Write the item to the file. """

        df.writeint(self.type)
        df.writestr(self.item_name)
        df.writefloat(self.weight)
        df.writeint(self.subtype)
        df.writeint(self.visibility)
        df.writeint(self.pictureid)
        df.writeint(self.value)
        df.writeint(self.canstack)
        df.writeint(self.quantity)
        df.writeint(self.basedamage)
        df.writeint(self.basearmor)
        df.writeint(self.attr_modified)
        df.writeint(self.attr_modifier)
        df.writeint(self.skill_modified)
        df.writeint(self.skill_modifier)
        df.writeint(self.hitpoint)
        df.writeint(self.mana)
        df.writeint(self.tohit)
        df.writeint(self.damage)
        df.writeint(self.armor)
        df.writeint(self.incr)
        df.writeint(self.flags)
        df.writestr(self.script)
        df.writestr(self.emptystr)
        df.writeint(self.zero1)
        df.writeint(self.duration)

    def hasborder(self):
        """ Decide whether or not a blue border would be drawn for this
            item, in the game. """

        return (self.attr_modified > 0 or
            self.skill_modified > 0 or
            self.hitpoint > 0 or
            self.mana > 0 or
            self.tohit > 0 or
            self.damage > 0 or
            self.armor > 0 or
            self.incr > 0 or
            self.flags > 0)

    def display(self, unknowns=False):
        """ Display a text representation of the item, indented. """

        global attrtable, skilltable, typetable, itemincrtable, flagstable

        if (self.type == 0):
            print "\t(none)"
        else:
            print "\t%s" % self.item_name
            if (typetable.has_key(self.type)):
                print "\tCategory: %s" % (typetable[self.type])
            else:
                print "\tCategory: 0x%08X" % (self.type)
            if (self.subtype != 0):
                if (skilltable.has_key(self.subtype)):
                    print "\tSubcategory: %s" % (skilltable[self.subtype])
                else:
                    print "\tSubcategory: 0x%08X" % (self.subtype)
            if (self.visibility == 3):
                print "\t(Note: this item has not been identified yet)"
            elif (self.visibility != 1):
                print "\tNOTICE: Unknown visibility ID: %d" % self.visibility
            print "\tPicture ID: %d" % self.pictureid
            print "\tValue: %d" % self.value
            if (self.basedamage > 0):
                print "\tBase Damage: %d" % self.basedamage
            if (self.basearmor > 0):
                print "\tBase Armor: %d" % self.basearmor
            if (self.attr_modified > 0):
                print "\tAttribute Modifier: +%d %s" % (self.attr_modifier, attrtable[self.attr_modified])
            if (self.skill_modified > 0):
                print "\tSkill Modifier: +%d %s" % (self.skill_modifier, skilltable[self.skill_modified])
            if (self.hitpoint > 0):
                print "\tSpecial: +%d Hit Points" % self.hitpoint
            if (self.mana > 0):
                print "\tSpecial: +%d Mana Points" % self.mana
            if (self.tohit > 0):
                print "\tSpecial: +%d ToHit" % self.tohit
            if (self.damage > 0):
                print "\tSpecial: +%d Damage" % self.damage
            if (self.armor > 0):
                print "\tSpecial: +%d Armor" % self.armor
            if (self.incr > 0):
                if (itemincrtable.has_key(self.incr)):
                    print "\tSpecial: %s +20%%" % itemincrtable[self.incr]
                else:
                    print "\tSpecial: 0x%08X" % self.incr
            if (self.flags > 0):
                if (flagstable.has_key(self.flags)):
                    print "\tSpecial: %s" % flagstable[self.flags]
                else:
                    print "\tSpecial: 0x%08X" % self.flags
            print "\tWeight: %0.1f lbs" % self.weight
            if (self.script != ''):
                print "\tScript: %s" % self.script
            if (self.duration > 0):
                print "\tDuration: %d" % self.duration
            if (self.canstack == 1):
                print "\tItem can be stacked (more than one per slot)"
            elif (self.canstack != 0):
                print "\tNOTICE: Unknown can-stack: %d" % self.canstack
            if (self.quantity > 1):
                print "\t(%d of this item in slot)" % self.quantity
            if (unknowns):
                print "\tUnknown fields:"
                print "\t\tZero 1: %d" % self.zero1
                print "\t\tEmpty String: %s" % self.emptystr
        print
