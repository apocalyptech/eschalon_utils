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

from EschalonB1 import skilltable, spelltable, dirtable, statustable, diseasetable

class MainCLI:

    def __init__(self, char):
        """ A fresh object, with no data. """

        self.char = char

    def display(self, unknowns=False):
        """ Print out a textual representation of the character."""

        global skilltable, dirtable, diseasetable

        char = self.char

        print "%s - Lvl %d %s %s %s" % (char.name, char.level, char.origin, char.axiom, char.classname)
        if (char.picid % 256 == 0):
            print "Profile Picture %d" % (int(char.picid / 256)+1)
        else:
            print "Profile Picture ID: %d" % char.picid
        print
        print "STR: %2d    INT: %2d" % (char.strength, char.intelligence)
        print "DEX: %2d    WIS: %2d" % (char.dexterity, char.wisdom)
        print "END: %2d    PCP: %2d" % (char.endurance, char.perception)
        print "SPD: %2d    CCN: %2d" % (char.speed, char.concentration)
        print

        print "HP: %d/%d   Mana: %d/%d" % (char.curhp, char.maxhp, char.curmana, char.maxmana)
        print "EXP: %d" % (char.experience)
        print
        
        print "CHARACTER STATUS"
        print "----------------"
        print
        for i in range(len(char.statuses)):
            if (char.statuses[i] > 0):
                if (statustable.has_key(i)):
                    print "\t* %s (Turns left: %d)" % (statustable[i], char.statuses[i])
                else:
                    print "\t* Status %d (unknown) (Turns left: %d)" % (i, char.statuses[i])
        for key in diseasetable.keys():
            if (char.disease & key == key):
                print "\t* Diseased: %s" % (diseasetable[key])
        print

        print "AVATAR GRAPHICS FX"
        print "------------------"
        print
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
        print

        print "ORIENTATION"
        print "-----------"
        print
        print "X: %d  Y: %d" % (char.xpos, char.ypos)
        if (dirtable.has_key(char.orientation)):
            print "Facing: %s" % dirtable[char.orientation]
        else:
            print "Facing: 0x%08X" % char.orientation
        print

        print "SKILLS"
        print "------"
        print
        for key in skilltable.keys():
            if char.skills.has_key(key) and char.skills[key] != 0:
                print "\t%s: %d" % (skilltable[key], char.skills[key])
        print

        print "SPELL JOURNAL"
        print "-------------"
        print
        for i in range(len(char.spells)):
            if (char.spells[i] == 1):
                print "\t* %s - %s" % (char.spelltype(i), spelltable[i])
        print

        print "READIED SPELLS"
        print "--------------"
        print
        i = 1
        for spell in char.readyslots:
            if (spell[0] != ''):
                print "\t%d - %s / Level %d" % (i%10, spell[0], spell[1])
            else:
                print "\t%d - (none)" % (i%10)
            i = i + 1
        print

        print "EQUIPPED ITEMS"
        print "--------------"
        print
        print "Quiver:"
        char.quiver.display(unknowns)
        print "Helm:"
        char.helm.display(unknowns)
        print "Cloak:"
        char.cloak.display(unknowns)
        print "Amulet:"
        char.amulet.display(unknowns)
        print "Torso:"
        char.torso.display(unknowns)
        print "Primary Weapon:"
        char.weap_prim.display(unknowns)
        print "Belt:"
        char.belt.display(unknowns)
        print "Gauntlet:"
        char.gauntlet.display(unknowns)
        print "Legs:"
        char.legs.display(unknowns)
        print "Ring 1:"
        char.ring1.display(unknowns)
        print "Ring 2:"
        char.ring2.display(unknowns)
        print "Shield:"
        char.shield.display(unknowns)
        print "Feet:"
        char.feet.display(unknowns)
        print "Alternate Weapon:"
        char.weap_alt.display(unknowns)
        
        print "INVENTORY"
        print "---------"
        print
        for row in range(10):
            for col in range(7):
                print "Row %d, Col %d:" % (row+1, col+1)
                if (row == 9 and col == 6):
                    print "\tGold: %d" % (char.gold)
                else:
                    char.inventory[row][col].display(unknowns)
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
            item.display()

        if (unknowns):
            print
            print "UNKNOWNS"
            print "--------"
            print
            char.unknown.display()
