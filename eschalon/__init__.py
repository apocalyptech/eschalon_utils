#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Book 1 Savefile Editor
# Copyright (C) 2008, 2009 CJ Kucera
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

# If app_name ever changes, we should update preferences/windows_prefsfile
# to provide an upgrade path
app_name = 'Eschalon Book 1 Savefile Editor'
version = '0.5.0'
url = 'http://apocalyptech.com/eschalon/'
authors = ['Main Code - CJ Kucera', 'Additional Code / Ideas - WR Goerlich', '', 'Some Icons by Axialis Team', 'see http://www.axialis.com/free/icons/']

__all__ = [ 'app_name', 'version', 'url', 'authors'
        'Savefile', 'Item', 'Unknowns', 'Character', 'MainGUI', 'LoadException',
        'Square', 'Mapscript', 'Undo',
        'attrtable', 'skilltable', 'typetable', 'itemincrtable', 'flagstable', 'spelltable', 'dirtable', 'statustable', 'traptable', 'containertable', 'diseasetable', 'objecttypetable', 'entitytable',
        'wall_list' ]

# Lookup tables
attrtable = {
        0x01: 'Strength',
        0x02: 'Dexterity',
        0x03: 'Endurance',
        0x04: 'Speed',
        0x05: 'Intelligence',
        0x06: 'Wisdom',
        0x07: 'Perception',
        0x08: 'Concentration'
    }
skilltable = {
        0x01: 'Alchemy',
        0x02: 'Divination',
        0x03: 'Elemental',
        0x04: 'Light Armor',
        0x05: 'Heavy Armor',
        0x06: 'Shields',
        0x07: 'Cartography',
        0x08: 'Dodge',
        0x09: 'Hide in Shadows',
        0x0A: 'Lore',
        0x0B: 'Meditation',
        0x0C: 'Mercantile',
        0x0D: 'Move Silently',
        0x0E: 'Pick Locks',
        0x0F: 'SkullDuggery',
        0x10: 'Spot Hidden',
        0x11: 'Survival',
        0x12: 'Unarmed Combat',
        0x13: 'Bludgeoning Weapons',
        0x14: 'Bows',
        0x15: 'Cleaving Weapons',
        0x16: 'Short Bladed Weapons',
        0x17: 'Swords',
        0x18: 'Thrown Weapons'
    }
typetable = {
        0x00: '(nothing)',
        0x01: 'Weapon',
        0x02: 'Arrow',
        0x03: 'Armor (Helm)',
        0x04: 'Armor (Cloak)',
        0x05: 'Armor (Torso)',
        0x06: 'Armor (Belt)',
        0x07: 'Armor (Gauntlet)',
        0x08: 'Armor (Legs)',
        0x09: 'Armor (Shield)',
        0x0A: 'Armor (Feet)',
        0x0B: 'Amulet',
        0x0C: 'Ring',
        0x0D: 'Magic',
        # 0x0E: Duration field displayed as "Charges" - dynamite of some sort
        0x0F: 'Potion',
        0x10: 'Reagent',
        0x11: 'Reactant',
        0x12: 'Miscellaneous',
        0x13: 'Lock Pick',
        0x14: 'Gem',
        # 0x15: No idea, just comes up n/a
        0x16: 'Consumable',
        0x17: 'Gold',
        0x18: 'n/a',
        0x19: 'Special',
        0x1A: 'Key'
        # Not sure if there's anything beyond here...
    }
itemincrtable = {
        0x01: 'Resist Elements',
        0x02: 'Resist Toxins',
        0x03: 'Resist Magick',
        0x04: 'Resist Disease'
    }
flagstable = {
        0x03: 'Poisoned'
    }
spelltable = {
        0: 'Bless',
        1: 'Cat\'s Eyes',
        2: 'Detox',
        3: 'Divine Heal',
        4: 'Entangle',
        5: 'Fleshboil',
        6: 'Leatherskin',
        7: 'Lore',
        8: 'Poison Spray',
        9: 'Nimbleness',
        10: 'Ogre Strength',
        11: 'Charm',
        12: 'Cure Disease',
        13: 'Enchanted Weapon',
        14: 'Haste',
        15: 'Sunder Flesh',
        16: 'Stoneskin',
        17: 'Turn Undead',
        18: 'Mass Boil',
        19: 'Smite',
        20: 'Dehex',
        21: 'Dancing Lights',
        22: 'Air Shield',
        23: 'Fire Dart',
        24: 'Gravedigger\'s Flame',
        25: 'Element Armor',
        26: 'Reveal Map',
        27: 'Predator Sight',
        28: 'Sonic Blast',
        29: 'Compress Atmosphere',
        30: 'Enkindled Weapon',
        31: 'Deep Freeze',
        32: 'Fireball',
        33: 'Chameleon',
        34: 'Lock Melt',
        35: 'Trapkill',
        36: 'Portal',
        37: 'Invisibility',
        38: 'Supernova'
    }
dirtable = {
        1: 'N',
        2: 'NE',
        3: 'E',
        4: 'SE',
        5: 'S',
        6: 'SW',
        7: 'W',
        8: 'NW'
    }
statustable = {
        0: 'Stunned',
        1: 'Air Shielded',
        2: 'Poisoned',
        3: 'Enchanted Weapon',
        4: 'Entangled',
        5: 'Cat\'s Eyes',
        6: 'Gravedigger\'s Flame',
        7: 'Bless',
        8: 'Haste',
        9: 'Ogre Strength',
        10: 'Invisible',
        11: 'Leatherskin',
        12: 'Nimbleness',
        13: 'Charmed',
        14: 'Reveal Map',
        15: 'Stoneskin',
        16: 'Keensight',
        17: 'Paralyzed',
        18: 'Scared',
        19: 'Enkindled Weapon',
        20: 'Elemental Armor',
        21: 'Chameleon',
        22: 'Predator Sight',
        23: 'Off-Balance',
        24: 'Mana Fortified',
        25: 'Greater Protection'
    }
traptable = {
        0: 'none',
        1: 'Poison Dart',
        2: 'Bixby\'s Noxious Cloud',
        3: 'Powder Blast',
        4: 'Festering Stew',
        5: 'Naga Bite',
        6: 'Acid Bath',
        7: 'Hellfire',
        8: 'Plaguebath'
    }
containertable = {
        0: 'none',
        1: 'closed',
        2: 'open',
        3: 'broken',
        4: 'toggle 1',
        5: 'toggle 2'
    }
# Right now this is the only one that appears to exist
scriptflags = {
        0x40: 'destructible'
    }
# Note that diseases are stored as bit flags
diseasetable = {
        0x0200: 'Dungeon Fever',
        0x0400: 'Rusty Knuckles',
        0x0800: 'Eye Fungus',
        0x1000: 'Blister Pox',
        0x2000: 'Insanity Fever',
        0x4000: 'Fleshrot',
        0x8000: 'Cursed'
    }

objecttypetable = {
        0: '(none)',
        1: 'Container (no open/close change - barrels, hives, sacs, coffins)',
        2: 'Container (corpses)',
        3: 'Container (chests, dressers, etc)',
        4: 'Container (only one in game, avoid this one)',
        5: 'Door',
        6: 'Map Link',
        7: 'Well, Lever, or other Misc Items',
        9: 'Message (wall decals - plaques, bookcases)',
        10: 'Message (walls - signs, gravestones)',
        11: 'Sealed Barrel',
        12: 'Miscellaneous Script',
        13: 'Sconce',
        14: 'Trap / Teleporter / Other tile-triggered actions',
        15: 'Blackpowder Keg',
        25: 'Light Source',
        30: 'Sound Generator (Inn)',
        31: 'Sound Generator (Church)',
        32: 'Sound Generator (Windy)',
        33: 'Sound Generator (Running Water)',
        34: 'Sound Generator (Magic Shop)',
        35: 'Sound Generator (Blacksmith)',
        36: 'Sound Generator (Woodland)',
        37: 'Sound Generator (Crowd)',
        38: 'Sound Generator (Waterfall)',
    }

class EntHelper(object):
    def __init__(self, name, health, gfxfile):
        self.name = name
        self.health = health
        self.gfxfile = gfxfile

# Entities
entitytable = {

        # Enemies
        0x01: EntHelper('Fanged Salamander', 9, 1),
        0x02: EntHelper('Bloodsipper', 17, 2),
        0x03: EntHelper('Raptor', 95, 3),
        0x04: EntHelper('Noximander', 35, 4),
        0x05: EntHelper('Fungal Slime', 25, 5),
        0x06: EntHelper('Walking Corpse', 55, 6),
        0x07: EntHelper('Acid Grubb', 70, 7),
        0x08: EntHelper('Timberland Giant', 140, 8),
        0x09: EntHelper('Goblin Hacker', 38, 9),
        0x0A: EntHelper('Goblin Archer', 45, 10),
        0x0B: EntHelper('Goblin Warlord', 75, 11),
        0x0C: EntHelper('Hive Drone', 40, 12),
        0x0D: EntHelper('Hive Queen', 100, 13),
        0x0E: EntHelper('Thug', 40, 14),
        0x0F: EntHelper('Dimensional Eye', 80, 15),
        0x10: EntHelper('Giant Arachnid', 70, 16),
        0x11: EntHelper('Dirachnid', 250, 17),
        0x12: EntHelper('Skeleton', 50, 18),
        0x13: EntHelper('Goblin Bombthug', 15, 19),
        0x14: EntHelper('Poltergeist', 60, 20),
        0x15: EntHelper('Barrea Mercenary', 90, 21),
        0x16: EntHelper('Taurax', 140, 22),
        0x17: EntHelper('Spire Guard', 300, 60),

        # NPCs
        0x33: EntHelper('Maddock', 15, 51),
        0x34: EntHelper('Michael', 36, 52),
        0x35: EntHelper('Farwick', 50, 53),
        0x36: EntHelper('Abygale', 25, 62),
        0x37: EntHelper('Eleanor *', 1, 55),
        0x38: EntHelper('Garrett *', 1, 50),
        0x39: EntHelper('Porter', 32, 56),
        0x3A: EntHelper('Oswell *', 1, 58),
        0x3B: EntHelper('Lilith', 130, 54),
        0x3C: EntHelper('Town Guard', 120, 60),
        0x3D: EntHelper('Gruzz', 16, 9),
        0x3E: EntHelper('Gatekeeper', 45, 60),
        0x3F: EntHelper('Eeru', 50, 65),
        0x40: EntHelper('Erik', 45, 53),
        0x41: EntHelper('Darkford Guard', 120, 60),
        0x42: EntHelper('Gunther', 85, 53),
        0x43: EntHelper('Leurik', 22, 65),
        0x44: EntHelper('Vault Master', 5, 9),
        0x45: EntHelper('Paul', 15, 51),
        0x46: EntHelper('Krista', 70, 57),
        0x47: EntHelper('Gamfari', 20, 64),
        0x48: EntHelper('Larrus *', 1, 66),
        0x49: EntHelper('Mary', 2, 63),
        0x4A: EntHelper('Vekkar *', 1, 67),
        0x4B: EntHelper('Jonathon', 36, 52),
        0x4C: EntHelper('Shady Character (1)', 90, 14),
        0x4D: EntHelper('Oolaseph *', 1, 54),
        0x4E: EntHelper('Vault Guard', 50, 60),
        0x4F: EntHelper('Vidar the Knife', 50, 14),
        0x50: EntHelper('Walter', 15, 68),
        0x51: EntHelper('Azure Guard', 120, 60),
        0x52: EntHelper('Captain Morgan', 120, 60),
        0x53: EntHelper('Erubor', 80, 69),
        0x54: EntHelper('Shadowmirk Acolyte', 15, 68),
        0x55: EntHelper('Phillip', 15, 65),
        0x56: EntHelper('Omar', 140, 8),
        0x57: EntHelper('Gramuk', 45, 70),
        0x58: EntHelper('Shady Character (2)', 110, 14),
        0x5A: EntHelper('Chancellor Malcolm *', 4, 71),
        0x5B: EntHelper('Sonya', 160, 59),
        0x5C: EntHelper('Aaron', 70, 61),
        0x5D: EntHelper('Penelope', 2, 62),
        0x5E: EntHelper('Siam', 80, 65),
        0x5F: EntHelper('William', 60, 51),
        0x60: EntHelper('Hesham', 60, 65)
    }

# Various lists to keep track of which objects should be walls
wall_list = {}
wall_list['floor_seethrough'] = range(83, 103) + [126]
wall_list['decal_blocked'] = [55]
wall_list['decal_seethrough'] = [52, 71, 83, 84, 96, 170]
wall_list['wall_blocked'] = (range(23, 31) + range(68, 72) + range(80, 85) +
    range(109, 112) + range(116, 121) + range(125, 144) +
    range(145, 156) + range(161, 214) + range(251, 256) + 
    [38, 40, 43, 49, 50, 58, 59, 79, 89, 101, 103, 105, 107, 215, 216, 219, 220])
wall_list['wall_seethrough'] = (range(1, 23) + range(31, 38) + range(44, 49) +
    range(51, 56) + range(60, 68) + range(72, 79) +
    range(85, 89) + range(112, 116) + range(121, 125) +
    [39, 41, 42, 57, 144, 214])

