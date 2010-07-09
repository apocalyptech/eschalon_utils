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

from eschalon import constants as c

class Item(object):
    """Class to hold a single Item's information."""

    book = None
    form_elements = []

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
        self.script = ''
        self.visibility = -1

        # Unknown fields.
        self.zero1 = -1
        self.emptystr = ''

        # Now, after doing all that, zero things out if we were told to do so
        if (zero):
            self.tozero()

    def tozero(self):
        """
        Resets all attributes to zero (or empty strings) - why exactly
        am I doing this here instead of just in the constructor?
        """
        self.type = 0
        self.subtype = 0
        self.weight = 0
        self.pictureid = 0
        self.value = 0
        self.canstack = 0
        self.quantity = 0
        self.basedamage = 0
        self.basearmor = 0
        self.visibility = 0
        self.zero1 = 0
        self.item_name = ''
        self.script = ''
        self.emptystr = ''

        # Call out to superclass zeroing
        self._sub_tozero()

    def _sub_tozero(self):
        """
        Function for superclasses to override with zeroing functions.
        """
        pass

    def replicate(self):

        newitem = Item.new(self.book)

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
        newitem.script = self.script
        newitem.visibility = self.visibility
        newitem.zero1 = self.zero1
        newitem.emptystr = self.emptystr

        # Call out to superclass replication
        self._sub_replicate(newitem)

        return newitem

    def _sub_replicate(self, newitem):
        """
        Stub for superclasses to override, to replicate specific vars
        """
        pass

    def equals(self, item):
        """
        Compare ourselves to another item object.  We're just
        checking if our values are the same, NOT if we're *actually*
        the same object.  Returns true for equality, false for inequality.
        """
        return (self._sub_equals(item) and
                self.type == item.type and
                self.subtype == item.subtype and
                self.item_name == item.item_name and
                self.weight == item.weight and
                self.pictureid == item.pictureid and
                self.value == item.value and
                self.canstack == item.canstack and
                self.quantity == item.quantity and
                self.basedamage == item.basedamage and
                self.basearmor == item.basearmor and
                self.script == item.script and
                self.visibility == item.visibility and
                self.zero1 == item.zero1 and
                self.emptystr == item.emptystr)

    def _sub_equals(self, item):
        """
        Stub for superclasses to override, to check for equality
        """
        pass

    def display(self, unknowns=False):
        """
        Display a text representation of the item, indented.
        This method has conditional statements for whether we're in Book 1 or
        Book 2.  Completely duplicating the whole thing in each specific class
        seemed kind of like overkill, whereas this seems lame.  Hm...
        """

        ret = []

        if (self.type == 0):
            ret.append("\t(none)")
        else:
            ret.append("\t%s" % self.item_name)
            if (c.typetable.has_key(self.type)):
                #ret.append("\tCategory: %s (0x%04X)" % (c.typetable[self.type], self.type))
                ret.append("\tCategory: %s" % (c.typetable[self.type]))
            else:
                ret.append("\tCategory: 0x%08X" % (self.type))
            if (self.subtype != 0):
                if (c.skilltable.has_key(self.subtype)):
                    ret.append("\tSubcategory: %s" % (c.skilltable[self.subtype]))
                else:
                    ret.append("\tSubcategory: 0x%08X" % (self.subtype))
            if self.book == 1:
                if (self.visibility == 3):
                    ret.append("\t(Note: this item has not been identified yet)")
                elif (self.visibility != 1):
                    ret.append("\tNOTICE: Unknown visibility ID: %d" % self.visibility)
            else:
                if (self.visibility > 1):
                    ret.append("\t(Note: this item has not been identified yet, difficulty %d)" % (self.visibility))
            ret.append("\tPicture ID: %d" % self.pictureid)
            ret.append("\tValue: %d" % self.value)
            if self.book == 2 and self.max_hp > 0:
                ret.append("\tCondition: %d%% (%d of %d)" % (self.cur_hp/float(self.max_hp)*100, self.cur_hp, self.max_hp))
            if (self.basedamage > 0):
                ret.append("\tBase Damage: %d" % self.basedamage)
            if (self.basearmor > 0):
                ret.append("\tBase Armor: %d" % self.basearmor)
            if self.book == 1:
                if (self.attr_modified > 0):
                    ret.append("\tAttribute Modifier: +%d %s" % (self.attr_modifier, c.attrtable[self.attr_modified]))
                if (self.skill_modified > 0):
                    ret.append("\tSkill Modifier: +%d %s" % (self.skill_modifier, c.skilltable[self.skill_modified]))
                if (self.hitpoint > 0):
                    ret.append("\tSpecial: +%d Hit Points" % self.hitpoint)
                if (self.mana > 0):
                    ret.append("\tSpecial: +%d Mana Points" % self.mana)
                if (self.tohit > 0):
                    ret.append("\tSpecial: +%d ToHit" % self.tohit)
                if (self.damage > 0):
                    ret.append("\tSpecial: +%d Damage" % self.damage)
                if (self.armor > 0):
                    ret.append("\tSpecial: +%d Armor" % self.armor)
                if (self.incr > 0):
                    if (c.itemincrtable.has_key(self.incr)):
                        ret.append("\tSpecial: %s +20%%" % c.itemincrtable[self.incr])
                    else:
                        ret.append("\tSpecial: 0x%08X" % self.incr)
                if (self.flags > 0):
                    if (c.flagstable.has_key(self.flags)):
                        ret.append("\tSpecial: %s" % c.flagstable[self.flags])
                    else:
                        ret.append("\tSpecial: 0x%08X" % self.flags)
            else:
                for i in range(1, 4):
                    modified_var = self.__dict__['attr_modified_%d' % (i)]
                    modifier_var = self.__dict__['attr_modifier_%d' % (i)]
                    if modified_var > 0 or modifier_var > 0:
                        if modified_var in c.itemeffecttable:
                            modified_var = c.itemeffecttable[modified_var]
                        ret.append("\tSpecial (%d): +%d %s" % (i, modifier_var, modified_var))
            ret.append("\tWeight: %0.1f lbs" % self.weight)
            if (self.script != ''):
                ret.append("\tScript: %s" % self.script)
            if self.book == 1:
                if (self.duration > 0):
                    ret.append("\tDuration: %d" % self.duration)
            if (self.canstack == 1):
                ret.append("\tItem can be stacked (more than one per slot)")
            elif (self.canstack != 0):
                ret.append("\tNOTICE: Unknown can-stack: %d" % self.canstack)
            if (self.quantity > 1):
                ret.append("\t(%d of this item in slot)" % self.quantity)
            if (unknowns):
                ret.append("\tUnknown fields:")
                ret.append("\t\tZero 1: %d" % self.zero1)
                ret.append("\t\tEmpty String: %s" % self.emptystr)
                if (self.book == 2):
                    ret.append("\t\tUnknown Flag: %d" % (self.unknownflag))
                    ret.append("\t\tUnknown Byte 1: %d" % (self.itemunknownc1))
        ret.append('')

        return "\n".join(ret)

    @staticmethod
    def new(book, zero=False):
        """
        Static method to initialize the appropriate type of Item and return it
        """
        if book == 1:
            return B1Item(zero)
        else:
            return B2Item(zero)

class B1Item(Item):
    """
    Item structure for Book 1
    """

    book = 1
    form_elements = [ 'item_b1_modifier_box',
            'duration_label', 'duration'
            ]

    def __init__(self, zero=False):
        
        # Attributes which only Book 1 has
        self.attr_modified = -1
        self.attr_modifier = -1
        self.skill_modified = -1
        self.skill_modifier = -1
        self.mana = -1
        self.tohit = -1
        self.damage = -1
        self.armor = -1
        self.incr = -1
        self.flags = -1
        self.hitpoint = -1
        self.duration = -1

        # Now the parent constructor
        super(B1Item, self).__init__(zero)

    def read(self, df):
        """ Given a file descriptor, read in the item. """

        self.type = df.readint()
        self.item_name = df.readstr()
        self.weight = df.readdouble()
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
        df.writedouble(self.weight)
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

    def _sub_replicate(self, newitem):
        """
        Replicate Book 1 specific item vars
        """
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
        newitem.duration = self.duration

    def _sub_tozero(self):
        """
        Zeroes out all Book 1 specific vars
        """
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
        self.duration = 0

    def _sub_equals(self, item):
        """
        Book 1 specific equality.
        """
        return (self.attr_modified == item.attr_modified and
                self.attr_modifier == item.attr_modifier and
                self.skill_modified == item.skill_modified and
                self.skill_modifier == item.skill_modifier and
                self.hitpoint == item.hitpoint and
                self.mana == item.mana and
                self.tohit == item.tohit and
                self.damage == item.damage and
                self.armor == item.armor and
                self.incr == item.incr and
                self.flags == item.flags and
                self.duration == item.duration)

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

class B2Item(Item):
    """
    Item structure for Book 2
    """

    book = 2
    form_elements = [ 'item_b2_modifier_box',
            'cur_hp_label', 'cur_hp',
            'max_hp_label', 'max_hp',
            'unknownflag', 'unknownflag_label',
            'itemunknownc1', 'itemunknownc1_label',
            'book2_item_picid_note'
            ]

    def __init__(self, zero=False):
        
        # Attributes which only Book 2 has
        self.unknownflag = -1
        self.max_hp = -1
        self.cur_hp = -1
        self.attr_modified_1 = -1
        self.attr_modifier_1 = -1
        self.attr_modified_2 = -1
        self.attr_modifier_2 = -1
        self.attr_modified_3 = -1
        self.attr_modifier_3 = -1

        self.itemunknownc1 = -1

        # Now the parent constructor
        super(B2Item, self).__init__(zero)

    def read(self, df):
        """ Given a file descriptor, read in the item. """

        self.type = df.readuchar()
        self.unknownflag = df.readuchar()
        self.item_name = df.readstr()
        self.weight = df.readfloat()
        self.subtype = df.readuchar()
        self.max_hp = df.readshort()
        self.cur_hp = df.readshort()
        self.itemunknownc1 = df.readuchar()
        self.visibility = df.readuchar()
        self.pictureid = df.readshort()
        self.value = df.readshort()
        self.canstack = df.readuchar()
        self.quantity = df.readshort()
        self.basedamage = df.readuchar()
        self.basearmor = df.readuchar()
        self.attr_modified_1 = df.readuchar()
        self.attr_modifier_1 = df.readuchar()
        self.attr_modified_2 = df.readuchar()
        self.attr_modifier_2 = df.readuchar()
        self.attr_modified_3 = df.readuchar()
        self.attr_modifier_3 = df.readsint()
        self.script = df.readstr()
        self.emptystr = df.readstr()
        self.zero1 = df.readshort()

    def write(self, df):
        """ Write the item to the file. """

        df.writeuchar(self.type)
        df.writeuchar(self.unknownflag)
        df.writestr(self.item_name)
        df.writefloat(self.weight)
        df.writeuchar(self.subtype)
        df.writeshort(self.max_hp)
        df.writeshort(self.cur_hp)
        df.writeuchar(self.itemunknownc1)
        df.writeuchar(self.visibility)
        df.writeshort(self.pictureid)
        df.writeshort(self.value)
        df.writeuchar(self.canstack)
        df.writeshort(self.quantity)
        df.writeuchar(self.basedamage)
        df.writeuchar(self.basearmor)
        df.writeuchar(self.attr_modified_1)
        df.writeuchar(self.attr_modifier_1)
        df.writeuchar(self.attr_modified_2)
        df.writeuchar(self.attr_modifier_2)
        df.writeuchar(self.attr_modified_3)
        df.writesint(self.attr_modifier_3)
        df.writestr(self.script)
        df.writestr(self.emptystr)
        df.writeshort(self.zero1)

    def _sub_replicate(self, newitem):
        """
        Replicate Book 2 specific item vars
        """
        newitem.unknownflag = self.unknownflag
        newitem.max_hp = self.max_hp
        newitem.cur_hp = self.cur_hp
        newitem.attr_modified_1 = self.attr_modified_1
        newitem.attr_modifier_1 = self.attr_modifier_1
        newitem.attr_modified_2 = self.attr_modified_2
        newitem.attr_modifier_2 = self.attr_modifier_2
        newitem.attr_modified_3 = self.attr_modified_3
        newitem.attr_modifier_3 = self.attr_modifier_3
        newitem.itemunknownc1 = self.itemunknownc1

    def _sub_tozero(self):
        """
        Zeroes out all Book 2 specific vars
        """
        self.unknownflag = 0
        self.max_hp = 0
        self.cur_hp = 0
        self.attr_modified_1 = 0
        self.attr_modifier_1 = 0
        self.attr_modified_2 = 0
        self.attr_modifier_2 = 0
        self.attr_modified_3 = 0
        self.attr_modifier_3 = 0
        self.itemunknownc1 = 0

    def _sub_equals(self, item):
        """
        Book 1 specific equality.
        """
        return (self.unknownflag == item.unknownflag and
                self.max_hp == item.max_hp and
                self.cur_hp == item.cur_hp and
                self.attr_modified_1 == item.attr_modified_1 and
                self.attr_modifier_1 == item.attr_modifier_1 and
                self.attr_modified_2 == item.attr_modified_2 and
                self.attr_modifier_2 == item.attr_modifier_2 and
                self.attr_modified_3 == item.attr_modified_3 and
                self.attr_modifier_3 == item.attr_modifier_3 and
                self.itemunknownc1 == item.itemunknownc1)

    def hasborder(self):
        """ Decide whether or not a blue border would be drawn for this
            item, in the game. """

        return (self.attr_modified_1 > 0 or
            self.attr_modified_2 > 0 or
            self.attr_modified_3 > 0)
