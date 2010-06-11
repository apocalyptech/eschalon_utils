#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Savefile Editor
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
from eschalon.character import Character
from eschalon.savefile import LoadException

class MainCLI(object):

    def __init__(self, options, prefs, req_book):
        """ A fresh object, with no data. """
        self.options = options
        self.prefs = prefs
        self.req_book = req_book

    def run(self):
        
        options = self.options

        # Load in our file
        try:
            char = Character.load(options['filename'], self.req_book)
            char.read()
            self.char = char
        except LoadException, e:
            print '"' + options['filename'] + '" could not be opened: %s' % (str(e))
            return False

        # The --list options will return automatically.  Everything
        # else will trigger a write once everything's done
        if (options['list']):
            return self.display(options['listoptions'], options['unknowns'])

        if (options['set_gold'] > 0):
            print 'Old Gold: %d' % (char.gold)
            char.setGold(options['set_gold'])
            print 'New Gold: %d' % (char.gold)

        if (options['set_hp_max'] > 0):
            print 'Old Max HP: %d' % (char.maxhp)
            char.setMaxHp(options['set_hp_max'])
            print 'New Max HP: %d' % (char.maxhp)

        if (options['set_hp_cur'] > 0):
            print 'Old Current HP: %d' % (char.curhp)
            char.setCurHp(options['set_hp_cur'])
            print 'New Current HP: %d' % (char.curhp)

        if (options['set_mana_max'] > 0):
            print 'Old Max Mana: %d' % (char.maxmana)
            char.setMaxMana(options['set_mana_max'])
            print 'New Max Mana: %d' % (char.maxmana)

        if (options['set_mana_cur'] > 0):
            print 'Old Current Mana: %d' % (char.curmana)
            char.setCurMana(options['set_mana_cur'])
            print 'New Current Mana: %d' % (char.curmana)

        if (options['rm_disease'] > 0):
            if char.book == 1:
                print 'Old Disease Flags: %04X' % (char.disease)
                char.clearDiseases();
                print 'New Disease Flags: %04X' % (char.disease)
            else:
                print 'Old Permanent Status Flags: %08X' % (char.permstatuses)
                char.clearDiseases();
                print 'New Permanent Status Flags: %08X' % (char.permstatuses)

        if (options['reset_hunger'] > 0):
            if char.book != 2:
                print 'Resetting hunger/thirst is only available for Book 2 characters'
            else:
                print 'Old Hunger/Thirst Levels: %d%% / %d%%' % (char.hunger/10.0, char.thirst/10.0)
                char.resetHunger()
                print 'New Hunger/Thirst Levels: %d%% / %d%%' % (char.hunger/10.0, char.thirst/10.0)
        
        # If we've gotten here, write the file
        char.write()
        
        # ... and return
        return True

    def display_header(self):
        """ Print out a textual representation of the character's name/level/orientation."""

        char = self.char
        if char.book == 1:
            print "%s - Lvl %d %s %s %s" % (char.name, char.level, char.origin, char.axiom, char.classname)
        else:
            str = ['%s - Lvl %d' % (char.name, char.level)]
            if char.gender in c.gendertable:
                str.append(c.gendertable[char.gender])
            else:
                str.append('(gender %d)' % (char.gender))
            if char.origin in c.origintable:
                str.append(c.origintable[char.origin])
            else:
                str.append('(origin %d)' % (char.origin))
            if char.axiom in c.axiomtable:
                str.append(c.axiomtable[char.axiom])
            else:
                str.append('(axiom %d)' % (char.axiom))
            if char.classname in c.classtable:
                str.append(c.classtable[char.classname])
            else:
                str.append('(class %d)' % (char.classname))
            print ' '.join(str)
        print

    def display_stats(self):
        """ Print out a textual representation of the character's stats."""

        char = self.char

        if char.book == 1:
            if (char.picid % 256 == 0):
                print "Profile Picture %d" % (int(char.picid / 256)+1)
            else:
                print "Profile Picture ID: %d" % char.picid
        else:
            if char.picid in c.picidtable:
                print "Profile Picture: %s" % (c.picidtable[char.picid])
            else:
                print "Profile Picture ID: %d" % char.picid
        print
        print "STR: %2d    INT: %2d     HP: %d/%d" % (char.strength, char.intelligence, char.curhp, char.maxhp)
        print "DEX: %2d    WIS: %2d     MP: %d/%d" % (char.dexterity, char.wisdom, char.curmana, char.maxmana)
        print "END: %2d    PCP: %2d    EXP: %d" % (char.endurance, char.perception, char.experience)
        print "SPD: %2d    CCN: %2d   GOLD: %d" % (char.speed, char.concentration, char.gold)
        if (char.book == 2):
            print "HUNGER: %2d%%    THIRST: %2d%%" % (char.hunger/10.0, char.thirst/10.0)
        print
        
        print "CHARACTER STATUS"
        print "----------------"
        print
        for i in range(len(char.statuses)):
            if (char.statuses[i] > 0):
                extra = ''
                if char.book == 2:
                    if (char.statuses_extra[i] > 0):
                        extra = ' (extra: %d)' % (char.statuses_extra[i])
                if (c.statustable.has_key(i)):
                    print "\t* %s (Turns left: %d)%s" % (c.statustable[i], char.statuses[i], extra)
                else:
                    print "\t* Status %d (unknown) (Turns left: %d)%s" % (i, char.statuses[i], extra)
        if char.book == 1:
            for key in c.diseasetable.keys():
                if (char.disease & key == key):
                    print "\t* Diseased: %s" % (c.diseasetable[key])
        print

        if char.book == 2:
            print '"PERMANENT" CHARATER STATUS'
            print "---------------------------"
            print
            for (mask, text) in c.permstatustable.items():
                if (char.permstatuses & mask == mask):
                    print "\t* %s" % (text)
            print

        print "SKILLS"
        print "------"
        print
        for key in c.skilltable.keys():
            if char.skills.has_key(key) and char.skills[key] != 0:
                print "\t%s: %d" % (c.skilltable[key], char.skills[key])
        print

    def display_avatar_info(self):
        """ Print out a textual representation of the character's avatar information."""

        char = self.char
        print "AVATAR GRAPHICS FX"
        print "------------------"
        print
        if char.book == 1:
            if (char.fxblock[0] == 1073741824 and
                char.fxblock[1] == 2111 and
                char.fxblock[2] == 2560 and
                char.fxblock[3] == 5120):
                print "Ordinary FX (no modifiers)"
            elif (char.fxblock[0] == 1803886340 and
                char.fxblock[1] == 61503 and
                char.fxblock[2] == 30720 and
                char.fxblock[3] == 15360):
                print "Gravedigger's Flame is On"
            elif (char.fxblock[0] == 1288490242 and
                char.fxblock[1] == 41023 and
                char.fxblock[2] == 38400 and
                char.fxblock[3] == 32000):
                print "Torch is On"
            elif (char.fxblock[0] == 1803886342 and
                char.fxblock[1] == 61503 and
                char.fxblock[2] == 38400 and
                char.fxblock[3] == 32000):
                print "Torch is On"
                print "Gravedigger's Flame is On"
            else:
                for i in char.fxblock:
                    print "\t* %d" % (i)
        else:
            for i in char.fxblock:
                print "\t* %d" % (i)
        print

        print "ORIENTATION"
        print "-----------"
        print
        print "X: %d  Y: %d" % (char.xpos, char.ypos)
        if (c.dirtable.has_key(char.orientation)):
            print "Facing: %s" % c.dirtable[char.orientation]
        else:
            print "Facing: 0x%08X" % char.orientation
        print

    def display_magic(self, unknowns=False):
        """ Print out a textual representation of the character's equipped magic stats."""

        char = self.char
        print "SPELL JOURNAL"
        print "-------------"
        print
        for i in range(len(char.spells)):
            if (char.spells[i] == 1):
                print "\t* %s - %s" % (c.spelltype[i], c.spelltable[i])
        print

        print "READIED SPELLS"
        print "--------------"
        print
        if char.book == 2:
            if char.readied_spell != '':
                print "\t(current) - %s / Level %d" % (char.readied_spell, char.readied_spell_lvl)
        i = 1
        for spell in char.readyslots:
            if (spell[0] != ''):
                print "\t%d - %s / Level %d" % (i%10, spell[0], spell[1])
            else:
                print "\t%d - (none)" % (i%10)
            i = i + 1
        print

        if char.book == 2:
            portal_locs = []
            for (slot, portal_loc) in enumerate(char.portal_locs):
                if portal_loc[1] != '':
                    portal_locs.append("\tSlot %d: %s (%s) at %d" % (slot+1, portal_loc[1], portal_loc[2], portal_loc[0]))
            if (len(portal_locs) > 0):
                print "BOUND PORTAL LOCATIONS"
                print "----------------------"
                print
                for portal_loc in portal_locs:
                    print portal_loc
                print

    def display_alchemy(self, unknowns=False):
        """
        Print out a textual representation of the character's alchemy recipe book.
        Only valid for Book 2
        """
        char = self.char
        if char.book == 2:
            print "ALCHEMY RECIPE BOOK"
            print "-------------------"
            print
            for (idx, recipe) in enumerate(char.alchemy_book):
                if recipe > 0:
                    print "\t* %s" % (c.alchemytable[idx])
            print

    def display_equip(self, unknowns=False):
        """ Print out a textual representation of the character's equipped items."""

        char = self.char
        print "EQUIPPED ITEMS"
        print "--------------"
        print
        print "Quiver:"
        print char.quiver.display(unknowns)
        print "Helm:"
        print char.helm.display(unknowns)
        print "Cloak:"
        print char.cloak.display(unknowns)
        print "Amulet:"
        print char.amulet.display(unknowns)
        print "Torso:"
        print char.torso.display(unknowns)
        print "Primary Weapon:"
        print char.weap_prim.display(unknowns)
        print "Belt:"
        print char.belt.display(unknowns)
        print "Gauntlet:"
        print char.gauntlet.display(unknowns)
        print "Legs:"
        print char.legs.display(unknowns)
        print "Ring 1:"
        print char.ring1.display(unknowns)
        print "Ring 2:"
        print char.ring2.display(unknowns)
        print "Shield:"
        print char.shield.display(unknowns)
        print "Feet:"
        print char.feet.display(unknowns)
        if char.book == 1:
            print "Alternate Weapon:"
            print char.weap_alt.display(unknowns)

        if char.book == 2:
            slotorder = [ 'Quiver', 'Helm', 'Cloak', 'Amulet', 'Torso',
                    'Weapon', 'Belt', 'Gauntlet', 'Legs', 'Ring 1', 'Ring 2',
                    'Shield', 'Feed' ]
            print
            print "EQUIPMENT SLOT 1"
            print "----------------"
            print
            for (idx, slot) in enumerate(slotorder):
                print "\t%s: %s" % (slotorder[idx], char.equip_slot_1[idx])
            print
            print "EQUIPMENT SLOT 2"
            print "----------------"
            print
            for (idx, slot) in enumerate(slotorder):
                print "\t%s: %s" % (slotorder[idx], char.equip_slot_2[idx])
            print
        
    def display_inventory(self, unknowns=False):
        """ Print out a textual representation of the character's inventory. """

        char = self.char

        if char.book == 2:
            print "KEYRING"
            print "-------"
            print
            for key in char.keyring:
                if key != '':
                    print "\t* %s" % (key)
            print

        print "INVENTORY"
        print "---------"
        print
        for row in range(char.inv_rows):
            for col in range(char.inv_cols):
                print "Row %d, Col %d:" % (row+1, col+1)
                if (row == (char.inv_rows-1) and col == (char.inv_cols-1)):
                    print "\tGold: %d" % (char.gold)
                else:
                    print char.inventory[row][col].display(unknowns)
        print "\tTorches: %d" % char.torches
        print "\tCurrent torch used for %d turns" % char.torchused
        print

        print "READY ITEMS"
        print "-----------"
        print
        i = 0
        for item in char.readyitems:
            i = i + 1
            print "Ready Item %d:" % (i)
            print item.display()

    def display(self, listoptions, unknowns=False):
        """ Print out a textual representation of the character."""

        self.display_header()

        if (listoptions['all'] or listoptions['stats']):
            self.display_stats()

        if (listoptions['all'] or listoptions['avatar']):
            self.display_avatar_info()

        if (listoptions['all'] or listoptions['magic']):
            self.display_magic(unknowns)

        if (listoptions['all'] or listoptions['alchemy']):
            self.display_alchemy(unknowns)

        if (listoptions['all'] or listoptions['equip']):
            self.display_equip(unknowns)

        if (listoptions['all'] or listoptions['inv']):
            self.display_inventory(unknowns)

        if (unknowns):
            print
            print "UNKNOWNS"
            print "--------"
            print
            print self.char.unknown.display()
