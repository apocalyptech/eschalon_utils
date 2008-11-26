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

from EschalonB1 import Savefile, Item, Unknowns, skilltable, spelltable, dirtable, statustable, diseasetable

class Character:
    """
    The base Character class.  Interestingly, some items which are NOT stored in
    the char file:
      * Which map the character's currently on (orientation/position ARE stored here though)
      * Time of day in the game world
      * Total time spent playing the game
    """

    def __init__(self, filename):
        """ A fresh object, with no data. """

        self.df = Savefile.Savefile(filename)
        self.name = ''
        self.origin = ''
        self.axiom = ''
        self.classname = ''
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
        for i in range(10):
            self.inventory.append([])
            for j in range(7):
                self.inventory[i].append(Item.Item())
        self.curinvcol = 0
        self.curinvrow = 0
        self.quiver = Item.Item()
        self.helm = Item.Item()
        self.cloak = Item.Item()
        self.amulet = Item.Item()
        self.torso = Item.Item()
        self.weap_prim = Item.Item()
        self.belt = Item.Item()
        self.gauntlet = Item.Item()
        self.legs = Item.Item()
        self.ring1 = Item.Item()
        self.ring2 = Item.Item()
        self.shield = Item.Item()
        self.feet = Item.Item()
        self.weap_alt = Item.Item()
        self.spells = []
        self.orientation = -1
        self.xpos = -1
        self.ypos = -1
        self.unknown = Unknowns.Unknowns()
        self.fxblock = []
        self.picid = -1
        self.statuses = []
        self.disease = -1

    def replicate(self):
        # Note that this could, theoretically, lead to contention issues, since
        # Savefile doesn't as yet lock the file.  So, er, be careful for now, I
        # guess.
        newchar = Character(self.df.filename)

        # Single vals (no need to do actual replication)
        newchar.name = self.name
        newchar.origin = self.origin
        newchar.axiom = self.axiom
        newchar.classname = self.classname
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
        newchar.disease = self.disease

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
        for i in range(10):
            for j in range(7):
                newchar.inventory[i][j] = self.inventory[i][j].replicate()
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
        newchar.weap_alt = self.weap_alt.replicate()
        newchar.unknown = self.unknown.replicate()

        # Now return our duplicated object
        return newchar

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
        if (self.curinvcol == 7):
            self.curinvcol = 0
            self.curinvrow = self.curinvrow + 1

    def addspell(self):
        """ Add a spell. """
        self.spells.append(self.df.readint())

    def read(self):
        """ Read in the whole save file from a file descriptor. """
        global skilltable

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
        for key in skilltable.keys():
            self.addskill(key, self.df.readint())

        # More stats
        self.maxhp = self.df.readint()
        self.maxmana = self.df.readint()
        self.curhp = self.df.readint()
        self.curmana = self.df.readint()
        self.experience = self.df.readint()
        self.level = self.df.readint()
        self.gold = self.df.readint()

        # Unknowns
        self.unknown.beginzero1 = self.df.readint()
        self.unknown.beginzero2 = self.df.readint()

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
        for i in range(70):
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

        # Unknown items
        for i in range(8):
            self.unknown.items[i].read(self.df)

        # For some reason, the last of the spells here.
        for i in range(4):
            self.addspell()

        # Read any extra data, just in case
        self.unknown.extradata = self.df.read()

        # Close the file
        self.df.close()

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

        # Unknowns
        self.df.writeint(self.unknown.beginzero1)
        self.df.writeint(self.unknown.beginzero2)

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

        # Unknown items
        for item in self.unknown.items:
            item.write(self.df)

        # For some reason, the last four spells
        for spell in self.spells[-4:]:
            self.df.writeint(spell)

        # Any extra data we might have
        if (len(self.unknown.extradata) > 0):
            self.df.writestr(self.unknown.extradata)

        # Clean up
        self.df.close()

    def spelltype(self, num):
        if (num < 21):
            return 'DI'
        else:
            return 'EL'

