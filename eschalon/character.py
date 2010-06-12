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

import struct
from eschalon import constants as c
from eschalon.savefile import Savefile, LoadException
from eschalon.item import Item
from eschalon.unknowns import B1Unknowns, B2Unknowns

class Character(object):
    """
    The base Character class.  Interestingly, some items which are NOT stored in
    the char file:
      * Which map the character's currently on (orientation/position ARE stored here though)
      * Time of day in the game world
      * Total time spent playing the game

    Note that the base class does not define read() and write() methods, which
    are left up to the specific Book classes (the theory being that the actual
    underlying formats can be rather different, and it doesn't really make sense
    to try and work around that.
    """

    book = None
    form_elements = []

    def __init__(self, df):
        """ A fresh object. """

        #self.book = c.book
        self.name = ''
        self.strength = -1
        self.dexterity = -1
        self.endurance = -1
        self.speed = -1
        self.intelligence = -1
        self.wisdom = -1
        self.perception = -1
        self.concentration = -1
        self.skills = {}
        self.maxhp = -1
        self.maxmana = -1
        self.curhp = -1
        self.curmana = -1
        self.experience = -1
        self.level = -1
        self.gold = -1
        self.torches = -1
        self.torchused = -1
        self.readyslots = []
        self.inventory = []
        for i in range(self.inv_rows):
            self.inventory.append([])
            for j in range(self.inv_cols):
                self.inventory[i].append(Item.new(c.book))
        self.readyitems = []
        for i in range(self.ready_rows * self.ready_cols):
            self.readyitems.append(Item.new(c.book))
        self.curinvcol = 0
        self.curinvrow = 0
        self.quiver = Item.new(c.book)
        self.helm = Item.new(c.book)
        self.cloak = Item.new(c.book)
        self.amulet = Item.new(c.book)
        self.torso = Item.new(c.book)
        self.weap_prim = Item.new(c.book)
        self.belt = Item.new(c.book)
        self.gauntlet = Item.new(c.book)
        self.legs = Item.new(c.book)
        self.ring1 = Item.new(c.book)
        self.ring2 = Item.new(c.book)
        self.shield = Item.new(c.book)
        self.feet = Item.new(c.book)
        self.spells = []
        self.orientation = -1
        self.xpos = -1
        self.ypos = -1
        self.fxblock = []
        self.picid = -1
        self.statuses = []
        self.extra_att_points = -1
        self.extra_skill_points = -1
        self.df = df

    def set_inv_size(self, rows, cols, ready_rows, ready_cols):
        """
        Sets the size of the inventory array
        """
        self.inv_rows = rows
        self.inv_cols = cols
        self.ready_rows = ready_rows
        self.ready_cols = ready_cols

    def replicate(self):
        # Note that this could, theoretically, lead to contention issues, since
        # Savefile doesn't as yet lock the file.  So, er, be careful for now, I
        # guess.
        newchar = Character.load(self.df.filename, self.book)

        # Single vals (no need to do actual replication)
        #newchar.book = self.book
        newchar.inv_rows = self.inv_rows
        newchar.inv_cols = self.inv_cols
        newchar.name = self.name
        newchar.strength = self.strength
        newchar.dexterity = self.dexterity
        newchar.endurance = self.endurance
        newchar.speed = self.speed
        newchar.intelligence = self.intelligence
        newchar.wisdom = self.wisdom
        newchar.perception = self.perception
        newchar.concentration = self.concentration
        newchar.maxhp = self.maxhp
        newchar.maxmana = self.maxmana
        newchar.curhp = self.curhp
        newchar.curmana = self.curmana
        newchar.experience = self.experience
        newchar.level = self.level
        newchar.gold = self.gold
        newchar.torches = self.torches
        newchar.torchused = self.torchused
        newchar.curinvcol = self.curinvcol
        newchar.curinvrow = self.curinvrow
        newchar.orientation = self.orientation
        newchar.xpos = self.xpos
        newchar.ypos = self.ypos
        newchar.picid = self.picid
        newchar.extra_att_points = self.extra_att_points
        newchar.extra_skill_points = self.extra_skill_points

        # Lists that need copying
        for val in self.spells:
            newchar.spells.append(val)
        for val in self.fxblock:
            newchar.fxblock.append(val)
        for val in self.statuses:
            newchar.statuses.append(val)

        # More complex lists that need copying
        for val in self.readyslots:
            newchar.readyslots.append([val[0], val[1]])

        # Dicts that need copying
        for key, val in self.skills.iteritems():
            newchar.skills[key] = val

        # Objects that need copying
        for i in range(self.inv_rows):
            for j in range(self.inv_cols):
                newchar.inventory[i][j] = self.inventory[i][j].replicate()
        for i in range(self.ready_rows * self.ready_cols):
            newchar.readyitems[i] = self.readyitems[i].replicate()
        newchar.quiver = self.quiver.replicate()
        newchar.helm = self.helm.replicate()
        newchar.cloak = self.cloak.replicate()
        newchar.amulet = self.amulet.replicate()
        newchar.torso = self.torso.replicate()
        newchar.weap_prim = self.weap_prim.replicate()
        newchar.belt = self.belt.replicate()
        newchar.gauntlet = self.gauntlet.replicate()
        newchar.legs = self.legs.replicate()
        newchar.ring1 = self.ring1.replicate()
        newchar.ring2 = self.ring2.replicate()
        newchar.shield = self.shield.replicate()
        newchar.feet = self.feet.replicate()

        # Call out to the subclass replication function
        self._sub_replicate(newchar)

        # Now return our duplicated object
        return newchar

    def _sub_replicate(self, newchar):
        """
        Just a stub function for superclasses to override, to replicate any
        superclass-specific data
        """
        pass

    def setGold(self,goldValue):
        """ Alter gold to new amount. """
        self.gold = goldValue

    def setMaxMana(self,manaValue):
        """
        Alter max mana value & set current to max.
        Note that equipped-item modifiers will raise the actual in-game
        maximums.
        """
        self.maxmana = manaValue
        if (self.curmana < manaValue):
            self.setCurMana(manaValue)

    def setCurMana(self,manaValue):
        """ Replenish mana to input value. """
        self.curmana = manaValue

    def setMaxHp(self,hpValue):
        """
        Alter max HP & set current to max.
        Note that equipped-item modifiers will raise the actual in-game
        maximums.
        """
        self.maxhp = hpValue
        if (self.curhp < hpValue):
            self.setCurHp(hpValue)

    def setCurHp(self,hpValue):
        """ Replenish HP to input value. """
        self.curhp = hpValue

    def clearDiseases(self):
        """
        Clear all diseases.  Also clears out severe injuries/curses/etc on Book 2 chars
        """
        if self.book == 1:
            self.disease = 0x0000
        else:
            self.permstatuses = self.permstatuses & 0xFFFF0000

    def resetHunger(self):
        """
        Resets hunger and thirst; only valid for Book 2 characters, of course.
        """
        if self.book == 2:
            self.hunger = 1000
            self.thirst = 1000

    def addskill(self, skillnum, level):
        """ Add a new skill at a given level. """
        self.skills[skillnum] = level

    def addreadyslot(self, spell, level):
        """ Add a new spell to a 'ready' slot. """
        self.readyslots.append([spell, level])

    def additem(self):
        """ Add a new item, assuming that the items are stored in a
            left-to-right, top-to-bottom format on the inventory screen. """
        self.inventory[self.curinvrow][self.curinvcol].read(self.df)
        self.curinvcol = self.curinvcol + 1
        if (self.curinvcol == self.inv_cols):
            self.curinvcol = 0
            self.curinvrow = self.curinvrow + 1

    @staticmethod
    def load(filename, book=None, req_book=None):
        """
        Static method to load a character file.  This will open the file once and
        read in a bit of data to determine whether this is a Book 1 character file or
        a Book 2 character file, and then call the appropriate constructor and
        return the object.  The individual Book constructors expect to be passed in
        an 
        """
        df = Savefile(filename)

        # First figure out what format to load, if needed
        if book is None:
            # The initial "zero" padding in Book 1 is four bytes, and only one byte in
            # Book 2.  Since the next bit of data is the character name, as a string,
            # if the second byte of the file is 00, we'll assume that it's a Book 1 file,
            # and Book 2 otherwise.
            try:
                df.open_r()
                initital = df.readuchar()
                second = df.readuchar()
                df.close()
            except (IOError, struct.error), e:
                raise LoadException(str(e))

            if second == 0:
                book = 1
            else:
                book = 2

        # See if we're required to conform to a specific book
        if (req_book is not None and book != req_book):
            raise LoadException('This utility can only load Book %d Character files; this file is from Book %d' % (req_book, book))

        # Now actually return the object
        if book == 1:
            c.switch_to_book(1)
            return B1Character(df)
        else:
            c.switch_to_book(2)
            return B2Character(df)

class B1Character(Character):
    """
    Book 1 Character definitions
    """

    book = 1
    form_elements = ['origin_label', 'origin_box',
            'axiom_label', 'axiom_box',
            'classname_label', 'classname_box',
            'picid_label', 'picid_hbox',
            'disease_label', 'disease_table',
            'gfx_preset_vbox',
            'weap_alt_label', 'weap_alt_container',
            'b1_gold_note'
            ]

    def __init__(self, df):
        self.set_inv_size(10, 7, 2, 4)
        super(B1Character, self).__init__(df)

        # Book 1 specific vars
        self.origin = ''
        self.axiom = ''
        self.classname = ''
        self.weap_alt = Item.new(1)
        self.disease = -1
        self.unknown = B1Unknowns()

    def read(self):
        """ Read in the whole save file from a file descriptor. """

        try:

            # Open the file
            self.df.open_r()

            # Start processing
            self.unknown.initzero = self.df.readint()

            # Character info
            self.name = self.df.readstr()
            self.unknown.charstring = self.df.readstr()
            self.origin = self.df.readstr()
            self.axiom = self.df.readstr()
            self.classname = self.df.readstr()
            self.unknown.charone = self.df.readint()
            self.strength = self.df.readint()
            self.dexterity = self.df.readint()
            self.endurance = self.df.readint()
            self.speed = self.df.readint()
            self.intelligence = self.df.readint()
            self.wisdom = self.df.readint()
            self.perception = self.df.readint()
            self.concentration = self.df.readint()

            # Skills
            for key in c.skilltable.keys():
                self.addskill(key, self.df.readint())

            # More stats
            self.maxhp = self.df.readint()
            self.maxmana = self.df.readint()
            self.curhp = self.df.readint()
            self.curmana = self.df.readint()
            self.experience = self.df.readint()
            self.level = self.df.readint()
            self.gold = self.df.readint()
            self.extra_att_points = self.df.readint()
            self.extra_skill_points = self.df.readint()

            # Character statuses
            for i in range(26):
                self.statuses.append(self.df.readint())
                self.unknown.sparseiblock.append(self.df.readint())

            # More Unknowns
            for i in range(17):
                self.unknown.iblock1.append(self.df.readint())
            for i in range(5):
                self.unknown.ssiblocks1.append(self.df.readstr())
                self.unknown.ssiblocks2.append(self.df.readstr())
                self.unknown.ssiblocki.append(self.df.readint())
            self.unknown.extstr1 = self.df.readstr()
            self.unknown.extstr2 = self.df.readstr()

            # Torches
            self.torches = self.df.readint()
            self.torchused = self.df.readint()

            # Further unknown
            self.unknown.anotherzero = self.df.readint()

            # Most of the spells (minus the last four Elemental)
            for i in range(35):
                self.addspell()

            # Readied Spells
            for i in range(10):
                self.addreadyslot(self.df.readstr(), self.df.readint())

            # Position/orientation
            self.orientation = self.df.readint()
            self.xpos = self.df.readint()
            self.ypos = self.df.readint()
            
            # These have *something* to do with your avatar, or effects that your
            # avatar has.  For instance, my avatar ordinarily looks like this:
            #    00 00 00 40    - 1073741824
            #    3F 08 00 00    - 2111
            #    00 0A 00 00    - 2560
            #    00 14 00 00    - 5120
            # When I have gravedigger's flame on, though, the GUI effect is described:
            #    04 1F 85 6B    - 1803886340
            #    3F F0 00 00    - 61503
            #    00 78 00 00    - 30720
            #    00 3C 00 00    - 15360
            # Torch on:
            #    02 CD CC 4C    - 1288490242
            #    3F A0 00 00    - 41023
            #    00 96 00 00    - 38400
            #    00 7D 00 00    - 32000
            # Gravedigger's + Torch on:
            #    06 1F 85 6B    - 1803886342
            #    3F F0 00 00    - 61503
            #    00 96 00 00    - 38400
            #    00 7D 00 00    - 32000
            # Invisible/Chameleon doesn't seem to apply here though.  Maybe just lighting fx?
            # Also, these certainly could be Not Actually ints; perhaps they're something else.
            for i in range(4):
                self.fxblock.append(self.df.readint())

            # An unknown, seems to be a multiple of 256
            self.unknown.anotherint = self.df.readint()

            # Character profile pic (multiple of 256, for some reason)
            self.picid = self.df.readint()

            # Disease flag
            self.disease = self.df.readint()

            # More Unknowns.  Apparently there's one 2-byte integer in here, too.
            self.unknown.shortval = self.df.readshort()
            self.unknown.emptystr = self.df.readstr()
            for i in range(21):
                self.unknown.iblock2.append(self.df.readint())
            self.unknown.preinvs1 = self.df.readstr()
            self.unknown.preinvs2 = self.df.readstr()
            self.unknown.preinvzero1 = self.df.readint()
            self.unknown.preinvzero2 = self.df.readint()

            # Inventory
            for i in range(self.inv_rows * self.inv_cols):
                self.additem()

            # Equipped
            self.quiver.read(self.df);
            self.helm.read(self.df);
            self.cloak.read(self.df);
            self.amulet.read(self.df);
            self.torso.read(self.df);
            self.weap_prim.read(self.df);
            self.belt.read(self.df);
            self.gauntlet.read(self.df);
            self.legs.read(self.df);
            self.ring1.read(self.df);
            self.ring2.read(self.df);
            self.shield.read(self.df);
            self.feet.read(self.df);
            self.weap_alt.read(self.df);

            # Readied items
            for i in range(8):
                self.readyitems[i].read(self.df)

            # For some reason, the last of the spells here.
            for i in range(4):
                try:
                    self.addspell()
                except struct.error, e:
                    # Apparently some versions don't always write these out,
                    # hack in some fake values if that's the case.
                    for j in range(4-i):
                        self.spells.append(0)
                    break

            # If there's extra data at the end, we likely don't have
            # a valid char file
            self.unknown.extradata = self.df.read()
            if (len(self.unknown.extradata)>0):
                raise LoadException('Extra data at end of file')

            # Close the file
            self.df.close()

        except (IOError, struct.error), e:
            raise LoadException(str(e))

    def write(self):
        """ Writes out the save file to the file descriptor. """
        
        # Open the file
        self.df.open_w()

        # Beginning
        self.df.writeint(self.unknown.initzero)

        # Char info
        self.df.writestr(self.name)
        self.df.writestr(self.unknown.charstring)
        self.df.writestr(self.origin)
        self.df.writestr(self.axiom)
        self.df.writestr(self.classname)
        self.df.writeint(self.unknown.charone)
        self.df.writeint(self.strength)
        self.df.writeint(self.dexterity)
        self.df.writeint(self.endurance)
        self.df.writeint(self.speed)
        self.df.writeint(self.intelligence)
        self.df.writeint(self.wisdom)
        self.df.writeint(self.perception)
        self.df.writeint(self.concentration)

        # Skills
        for skill in self.skills.values():
            self.df.writeint(skill)

        # More stats
        self.df.writeint(self.maxhp)
        self.df.writeint(self.maxmana)
        self.df.writeint(self.curhp)
        self.df.writeint(self.curmana)
        self.df.writeint(self.experience)
        self.df.writeint(self.level)
        self.df.writeint(self.gold)
        self.df.writeint(self.extra_att_points)
        self.df.writeint(self.extra_skill_points)

        # Statuses
        for i in range(len(self.statuses)):
            self.df.writeint(self.statuses[i])
            self.df.writeint(self.unknown.sparseiblock[i])

        # More unknowns
        for unknown in self.unknown.iblock1:
            self.df.writeint(unknown)
        for i in range(len(self.unknown.ssiblocks1)):
            self.df.writestr(self.unknown.ssiblocks1[i])
            self.df.writestr(self.unknown.ssiblocks2[i])
            self.df.writeint(self.unknown.ssiblocki[i])
        self.df.writestr(self.unknown.extstr1)
        self.df.writestr(self.unknown.extstr2)

        # Torches
        self.df.writeint(self.torches)
        self.df.writeint(self.torchused)

        # Further unknown
        self.df.writeint(self.unknown.anotherzero)

        # Most of the spells
        for spell in self.spells[:-4]:
            self.df.writeint(spell)

        # Readied Spells
        for slot in self.readyslots:
            self.df.writestr(slot[0])
            self.df.writeint(slot[1])

        # Position/orientation
        self.df.writeint(self.orientation)
        self.df.writeint(self.xpos)
        self.df.writeint(self.ypos)

        # Visual FX
        for fx in self.fxblock:
            self.df.writeint(fx)

        # Unknown
        self.df.writeint(self.unknown.anotherint)

        # Profile pic
        self.df.writeint(self.picid)

        # Disease
        self.df.writeint(self.disease)

        # More unknowns
        self.df.writeshort(self.unknown.shortval)
        self.df.writestr(self.unknown.emptystr)
        for val in self.unknown.iblock2:
            self.df.writeint(val)
        self.df.writestr(self.unknown.preinvs1)
        self.df.writestr(self.unknown.preinvs2)
        self.df.writeint(self.unknown.preinvzero1)
        self.df.writeint(self.unknown.preinvzero2)

        # Inventory
        for row in self.inventory:
            for item in row:
                item.write(self.df)

        # Equipped
        self.quiver.write(self.df);
        self.helm.write(self.df);
        self.cloak.write(self.df);
        self.amulet.write(self.df);
        self.torso.write(self.df);
        self.weap_prim.write(self.df);
        self.belt.write(self.df);
        self.gauntlet.write(self.df);
        self.legs.write(self.df);
        self.ring1.write(self.df);
        self.ring2.write(self.df);
        self.shield.write(self.df);
        self.feet.write(self.df);
        self.weap_alt.write(self.df);

        # Readied items
        for item in self.readyitems:
            item.write(self.df)

        # For some reason, the last four spells
        for spell in self.spells[-4:]:
            self.df.writeint(spell)

        # Any extra data we might have
        if (len(self.unknown.extradata) > 0):
            self.df.writestr(self.unknown.extradata)

        # Clean up
        self.df.close()

    def _sub_replicate(self, newchar):
        """
        Replicate our Book 1 specific data
        """
        newchar.origin = self.origin
        newchar.axiom = self.axiom
        newchar.classname = self.classname
        newchar.weap_alt = self.weap_alt.replicate()
        newchar.disease = self.disease
        newchar.unknown = self.unknown.replicate()

    def addspell(self):
        """ Add a spell. """
        self.spells.append(self.df.readint())

class B2Character(Character):
    """
    Book 2 Character definitions
    """

    book = 2
    form_elements = [ 'gender_label', 'gender',
            'b2origin_label', 'b2origin',
            'b2axiom_label', 'b2axiom',
            'b2classname_label', 'b2classname',
            'b2picid_label', 'b2picid',
            'hunger_label', 'hunger_hbox',
            'thirst_label', 'thirst_hbox',
            'b2_second_effect_var_label',
            'permstatus_alignment', 'permstatus_label',
            'fxblock_4_label', 'fxblock_4',
            'fxblock_5_label', 'fxblock_5',
            'fxblock_6_label', 'fxblock_6',
            'readied_spell_label', 'readied_spell_box', 'readied_spell_lvl',
            'b2_portal_header', 'b2_portal_body',
            'alchemy_tab',
            'ready_8_label', 'ready_8_container',
            'ready_9_label', 'ready_9_container',
            'inv_0_7_label', 'inv_0_7_container',
            'inv_1_7_label', 'inv_1_7_container',
            'inv_2_7_label', 'inv_2_7_container',
            'inv_3_7_label', 'inv_3_7_container',
            'inv_4_7_label', 'inv_4_7_container',
            'inv_5_7_label', 'inv_5_7_container',
            'inv_6_7_label', 'inv_6_7_container',
            'inv_7_7_label', 'inv_7_7_container',
            'inv_8_7_label', 'inv_8_7_container',
            'inv_9_7_label', 'inv_9_7_container',
            'b2_gold_note',
            'keyring_label', 'keyring_align'
            ]

    def __init__(self, df):
        self.set_inv_size(10, 8, 2, 5)
        super(B2Character, self).__init__(df)

        # Book 2 specific vars
        self.gender = -1
        self.origin = -1
        self.axiom = -1
        self.classname = -1
        self.hunger = -1
        self.thirst = -1
        self.portal_locs = []
        self.readied_spell = ''
        self.readied_spell_lvl = -1
        self.alchemy_book = []
        self.statuses_extra = []
        self.permstatuses = -1
        self.keyring = []
        self.equip_slot_1 = []
        self.equip_slot_2 = []
        self.unknown = B2Unknowns()

    def read(self):
        """ Read in the whole save file from a file descriptor. """

        try:

            # Open the file
            self.df.open_r()

            # Start processing
            self.unknown.initzero = self.df.readuchar()

            # Character info
            self.name = self.df.readstr()
            self.gender = self.df.readuchar()
            self.origin = self.df.readuchar()
            self.axiom = self.df.readuchar()
            self.classname = self.df.readuchar()
            self.unknown.version = self.df.readuchar()
            if self.unknown.version == 1:
                raise LoadException('This savegame was probably saved in v1.02 of Book 2, only 1.03 and higher is supported')
            self.strength = self.df.readuchar()
            self.dexterity = self.df.readuchar()
            self.endurance = self.df.readuchar()
            self.speed = self.df.readuchar()
            self.intelligence = self.df.readuchar()
            self.wisdom = self.df.readuchar()
            self.perception = self.df.readuchar()
            self.concentration = self.df.readuchar()

            # Skills
            for key in sorted(c.skilltable.keys()):
                self.addskill(key, self.df.readuchar())

            # More stats
            self.extra_att_points = self.df.readuchar()
            self.extra_skill_points = self.df.readuchar()
            self.curhp = self.df.readint()
            self.curmana = self.df.readint()
            self.maxhp = self.df.readint()
            self.maxmana = self.df.readint()
            self.experience = self.df.readint()
            self.level = self.df.readint()
            self.hunger = self.df.readint()
            self.thirst = self.df.readint()

            # FX block
            for i in range(7):
                self.fxblock.append(self.df.readint())

            # Non-permanent Chracter Statuses (will expire automatically)
            for i in range(26):
                self.statuses.append(self.df.readint())
                self.statuses_extra.append(self.df.readint())

            # Portal anchor locations
            for i in range(6):
                portal_anchor = []
                portal_anchor.append(self.df.readint())
                portal_anchor.append(self.df.readstr())
                portal_anchor.append(self.df.readstr())
                self.portal_locs.append(portal_anchor)

            # Unknown
            self.unknown.zero1 = self.df.readuchar()

            # Spells
            for i in range(len(c.spelltable)):
                self.addspell()

            # Currently-readied spell
            self.readied_spell = self.df.readstr()
            self.readied_spell_lvl = self.df.readuchar()

            # Readied Spells
            for i in range(10):
                self.addreadyslot(self.df.readstr(), self.df.readuchar())

            # Alchemy Recipes
            for i in range(25):
                self.addalchemy()

            # Some unknown values (zeroes so far)
            for i in range(14):
                self.unknown.fourteenzeros.append(self.df.readint())

            # Position/orientation
            self.orientation = self.df.readuchar()
            self.xpos = self.df.readint()
            self.ypos = self.df.readint()

            # Some unknowns
            for i in range(5):
                self.unknown.strangeblock.append(self.df.readuchar())
            self.unknown.unknowni1 = self.df.readint()
            self.unknown.unknowni2 = self.df.readint()
            self.unknown.unknowni3 = self.df.readint()
            self.unknown.usually_one = self.df.readuchar()

            # Permanent Statuses (bitfield)
            self.permstatuses = self.df.readint()

            # More stats
            self.picid = self.df.readint()
            self.gold = self.df.readint()
            self.torches = self.df.readint()
            self.torchused = self.df.readint()

            # Keyring
            for i in range(20):
                self.keyring.append(self.df.readstr())

            # More unknowns
            self.unknown.unknowns1 = self.df.readshort()
            self.unknown.unknownstr1 = self.df.readstr()
            for i in range(29):
                self.unknown.twentyninezeros.append(self.df.readuchar())
            self.unknown.unknownstr2 = self.df.readstr()
            self.unknown.unknownstr3 = self.df.readstr()
            self.unknown.unknowns2 = self.df.readshort()

            # Inventory
            for i in range(self.inv_rows * self.inv_cols):
                self.additem()

            # Equipped
            self.quiver.read(self.df);
            self.helm.read(self.df);
            self.cloak.read(self.df);
            self.amulet.read(self.df);
            self.torso.read(self.df);
            self.weap_prim.read(self.df);
            self.belt.read(self.df);
            self.gauntlet.read(self.df);
            self.legs.read(self.df);
            self.ring1.read(self.df);
            self.ring2.read(self.df);
            self.shield.read(self.df);
            self.feet.read(self.df);

            # Readied items
            for i in range(10):
                self.readyitems[i].read(self.df)

            # Equipment Slots
            for i in range(13):
                self.equip_slot_1.append(self.df.readstr())
                self.equip_slot_2.append(self.df.readstr())

            # If there's extra data at the end, we likely don't have
            # a valid char file
            self.unknown.extradata = self.df.read()
            if (len(self.unknown.extradata)>0):
                raise LoadException('Extra data at end of file')

            # Close the file
            self.df.close()

        except (IOError, struct.error), e:
            raise LoadException(str(e))

    def write(self):
        """ Writes out the save file. """

        self.df.open_w()

        # Initial Zero
        self.df.writeuchar(self.unknown.initzero)

        # Character info
        self.df.writestr(self.name)
        self.df.writeuchar(self.gender)
        self.df.writeuchar(self.origin)
        self.df.writeuchar(self.axiom)
        self.df.writeuchar(self.classname)
        self.df.writeuchar(self.unknown.version)
        self.df.writeuchar(self.strength)
        self.df.writeuchar(self.dexterity)
        self.df.writeuchar(self.endurance)
        self.df.writeuchar(self.speed)
        self.df.writeuchar(self.intelligence)
        self.df.writeuchar(self.wisdom)
        self.df.writeuchar(self.perception)
        self.df.writeuchar(self.concentration)

        # Skills
        for skill in self.skills.values():
            self.df.writeuchar(skill)

        # More stats
        self.df.writeuchar(self.extra_att_points)
        self.df.writeuchar(self.extra_skill_points)
        self.df.writeint(self.curhp)
        self.df.writeint(self.curmana)
        self.df.writeint(self.maxhp)
        self.df.writeint(self.maxmana)
        self.df.writeint(self.experience)
        self.df.writeint(self.level)
        self.df.writeint(self.hunger)
        self.df.writeint(self.thirst)

        # FX Block
        for fx in self.fxblock:
            self.df.writeint(fx)

        # Non-permanent statuses
        for (status, extra) in zip(self.statuses, self.statuses_extra):
            self.df.writeint(status)
            self.df.writeint(extra)

        # Portal anchor locations
        for anchor in self.portal_locs:
            self.df.writeint(anchor[0])
            self.df.writestr(anchor[1])
            self.df.writestr(anchor[2])

        # Unknown
        self.df.writeuchar(self.unknown.zero1)

        # Spells
        for spell in self.spells:
            self.df.writeuchar(spell)

        # Readied Spells
        self.df.writestr(self.readied_spell)
        self.df.writeuchar(self.readied_spell_lvl)
        for (spell, level) in self.readyslots:
            self.df.writestr(spell)
            self.df.writeuchar(level)

        # Alchemy Recipes
        for recipe in self.alchemy_book:
            self.df.writeint(recipe)

        # Unknowns
        for zero in self.unknown.fourteenzeros:
            self.df.writeint(zero)

        # Position/orientation
        self.df.writeuchar(self.orientation)
        self.df.writeint(self.xpos)
        self.df.writeint(self.ypos)

        # More unknowns
        for val in self.unknown.strangeblock:
            self.df.writeuchar(val)
        self.df.writeint(self.unknown.unknowni1)
        self.df.writeint(self.unknown.unknowni2)
        self.df.writeint(self.unknown.unknowni3)
        self.df.writeuchar(self.unknown.usually_one)

        # Permanent statuses
        self.df.writeint(self.permstatuses)

        # More stats
        self.df.writeint(self.picid)
        self.df.writeint(self.gold)
        self.df.writeint(self.torches)
        self.df.writeint(self.torchused)

        # Keyring
        for key in self.keyring:
            self.df.writestr(key)

        # Yet more unknowns
        self.df.writeshort(self.unknown.unknowns1)
        self.df.writestr(self.unknown.unknownstr1)
        for zero in self.unknown.twentyninezeros:
            self.df.writeuchar(zero)
        self.df.writestr(self.unknown.unknownstr2)
        self.df.writestr(self.unknown.unknownstr3)
        self.df.writeshort(self.unknown.unknowns2)

        # Inventory
        for row in self.inventory:
            for item in row:
                item.write(self.df)

        # Equipped
        self.quiver.write(self.df);
        self.helm.write(self.df);
        self.cloak.write(self.df);
        self.amulet.write(self.df);
        self.torso.write(self.df);
        self.weap_prim.write(self.df);
        self.belt.write(self.df);
        self.gauntlet.write(self.df);
        self.legs.write(self.df);
        self.ring1.write(self.df);
        self.ring2.write(self.df);
        self.shield.write(self.df);
        self.feet.write(self.df);

        # Readied items
        for item in self.readyitems:
            item.write(self.df)

        # Equipment Slots
        for (slot1, slot2) in zip(self.equip_slot_1, self.equip_slot_2):
            self.df.writestr(slot1)
            self.df.writestr(slot2)

        # Any extra data we might have
        if (len(self.unknown.extradata) > 0):
            self.df.writestr(self.unknown.extradata)

        # Clean up
        self.df.close()

    def _sub_replicate(self, newchar):
        """
        Replicate our Book 2 specific data
        """
        newchar.gender = self.gender
        newchar.origin = self.origin
        newchar.axiom = self.axiom
        newchar.classname = self.classname
        newchar.thirst = self.thirst
        newchar.hunger = self.hunger
        newchar.permstatuses = self.permstatuses
        newchar.readied_spell = self.readied_spell
        newchar.readied_spell_lvl = self.readied_spell_lvl

        # Lists
        for recipe in self.alchemy_book:
            newchar.alchemy_book.append(recipe)
        for extra in self.statuses_extra:
            newchar.statuses_extra.append(extra)
        for key in self.keyring:
            newchar.keyring.append(key)
        for equip in self.equip_slot_1:
            newchar.equip_slot_1.append(equip)
        for equip in self.equip_slot_2:
            newchar.equip_slot_2.append(equip)

        # More complex lists
        for (one, two, three) in self.portal_locs:
            newchar.portal_locs.append([one, two, three])

        # Objects
        newchar.unknown = self.unknown.replicate()

    def addalchemy(self):
        """ Add an alchemy recipe. """
        self.alchemy_book.append(self.df.readint())

    def addspell(self):
        """ Add a spell. """
        self.spells.append(self.df.readuchar())
