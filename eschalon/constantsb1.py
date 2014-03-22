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

__all__ = [ 'B1Constants' ]

class B1Constants:

    book = 1

    # Equivalent floor numbers to use when converting maps to B3
    b3_floor_conversions = {
            1: 9, 2: 12, 3: 5, 4: 6, 5: 13, 6: 14, 7: 33, 8: 26, 9: 1,
            10: 2, 11: 3, 12: 4, 13: 59, 14: 59, 15: 44, 16: 22, 17: 23,
            18: 23, 19: 74, 20: 66, 21: 10, 22: 11, 23: 57, 24: 31, 25: 61,
            26: 60, 27: 48, 28: 58, 29: 57, 30: 30, 31: 69, 32: 70, 33: 71,
            34: 43, 35: 44, 36: 39, 37: 50, 38: 56, 39: 52, 40: 22, 41: 23,
            42: 38, 43: 60, 44: 61, 45: 49, 46: 41, 47: 52, 48: 59, 49: 66,
            50: 74, 51: 47, 52: 49, 53: 63, 54: 50, 60: 73, 61: 17, 62: 18,
            63: 19, 64: 54, 65: 66, 66: 52, 67: 24, 68: 25, 69: 26, 70: 46,
            71: 67, 72: 59, 73: 69, 74: 70, 75: 71, 76: 72, 77: 69, 78: 70,
            79: 5, 80: 6, 81: 7, 82: 8, 124: 20, 125: 28, 126: 113, 127: 125,
            128: 128, 129: 121, 130: 122, 131: 114, 132: 115, 133: 127,
            134: 126, 135: 123, 136: 124, 137: 116, 138: 117, 139: 113,
            140: 122, 141: 123, 142: 113, 143: 121, 144: 122, 145: 118,
            146: 119, 147: 120,
    }
    # Floor types that should be replaced with (floor) decals instead
    b3_floor_to_decal = {
            55: 154, 56: 170, 57: 155, 58: 156, 59: 171,
    }
    # Equivalent wall numbers to use when converting maps to B3
    b3_wall_conversions = {
            1: 151, 2: 160, 3: 14, 4: 75, 5: 13, 6: 50, 7: 17, 8: 18, 9: 19,
            10: 20, 11: 21, 12: 22, 13: 23, 14: 24, 15: 91, 16: 92, 17: 93,
            18: 94, 19: 67, 20: 68, 21: 65, 22: 66, 23: 1, 24: 2, 25: 70,
            26: 69, 27: 5, 28: 6, 29: 3, 30: 4, 31: 28, 32: 29, 33: 31, 34:
            30, 35: 45, 36: 46, 37: 117, 38: 128, 39: 32, 40: 52, 41: 100,
            42: 35, 43: 57, 44: 111, 45: 408, 46: 37, 47: 38, 48: 36, 49:
            11, 50: 12, 51: 134, 52: 135, 53: 118, 54: 55, 55: 56, 56: 25,
            57: 73, 58: 71, 59: 72, 60: 101, 61: 333, 62: 126, 63: 124, 64:
            126, 65: 124, 66: 125, 67: 7, 69: 5, 70: 42, 71: 43, 72: 102,
            73: 48, 74: 47, 75: 62, 76: 64, 77: 63, 78: 61, 79: 83, 80: 84,
            81: 85, 82: 86, 83: 85, 85: 414, 86: 166, 87: 150, 88: 150, 89:
            40, 90: 0, 91: 129, 92: 133, 93: 115, 94: 131, 95: 133, 96: 97,
            101: 266, 102: 267, 103: 268, 104: 269, 105: 282, 106: 283, 107:
            284, 108: 285, 109: 330, 110: 331, 111: 399, 112: 316, 113: 319,
            114: 318, 115: 125, 116: 332, 117: 270, 118: 271, 119: 367, 120:
            314, 121: 349, 122: 351, 123: 95, 124: 96, 125: 408, 126: 409,
            127: 405, 128: 405, 129: 406, 130: 254, 131: 254, 132: 414, 133:
            314, 138: 413, 139: 363, 140: 383, 141: 382, 142: 254, 143: 381,
            144: 407, 145: 398, 146: 397, 147: 397, 148: 404, 149: 81, 150:
            146, 151: 145, 152: 334, 153: 253, 154: 349, 155: 333, 161: 272,
            162: 273, 163: 274, 164: 275, 165: 276, 166: 277, 167: 278, 168:
            279, 169: 280, 170: 281, 171: 288, 172: 289, 173: 290, 174: 291,
            175: 292, 176: 293, 177: 294, 178: 295, 179: 296, 180: 297, 181:
            368, 182: 369, 183: 370, 184: 371, 185: 372, 186: 373, 187: 374,
            188: 375, 189: 376, 190: 377, 191: 256, 192: 257, 193: 258, 194:
            259, 195: 260, 196: 261, 197: 262, 198: 263, 199: 264, 200: 265,
            201: 352, 202: 353, 203: 354, 204: 355, 205: 356, 206: 357, 207:
            358, 208: 359, 209: 360, 210: 361, 211: 298, 212: 299, 213: 300,
            214: 379, 215: 364, 216: 365, 219: 380, 220: 410, 251: 254, 252:
            252, 253: 251, 254: 253, 255: 132,
    }
    # Wall types that should be replaced with (wall) decals instead
    b3_wall_to_decal = {
            134: 133, 135: 134, 136: 135, 137: 135, 215: 81, 216: 97, 217:
            82, 218: 98,
    }

    # Equivalent floor decal numbers to use when converting maps to B3
    b3_floor_decal_conversions = {
            1: 9, 2: 236, 3: 23, 4: 7, 5: 185, 6: 25, 7: 55, 8: 194, 9: 56,
            10: 222, 11: 221, 12: 196, 13: 115, 14: 116, 15: 117, 16: 118,
            17: 119, 18: 120, 19: 121, 20: 39, 21: 9, 22: 25, 23: 24, 26:
            209, 27: 210, 28: 211, 29: 212, 30: 228, 31: 72, 32: 88, 33: 60,
            34: 12, 35: 60, 36: 12, 37: 97, 38: 8, 39: 8, 41: 44, 42: 28,
            43: 98, 44: 210, 49: 99, 52: 101, 53: 166, 54: 166, 55: 158, 58:
            135, 59: 136, 71: 100, 73: 200, 74: 167, 75: 104, 76: 168, 77:
            184, 78: 217, 79: 198, 80: 197, 81: 181, 82: 200, 83: 215, 84:
            214, 86: 137, 87: 61, 88: 225, 89: 226, 90: 227, 91: 103, 92: 102, 93:
            104, 94: 13, 95: 87, 96: 15, 97: 19, 98: 20, 99: 18, 100: 17,
            101: 4, 102: 3, 103: 6, 104: 5, 105: 2, 106: 1, 107: 49, 108:
            51, 109: 52, 110: 50, 111: 3, 112: 5, 113: 3, 114: 6, 115: 73,
            116: 241, 117: 242, 118: 243, 119: 241, 120: 166, 121: 73, 122:
            134, 123: 150, 124: 151, 125: 152, 126: 37, 127: 179, 128: 178,
            129: 177, 130: 180, 131: 163, 132: 161, 133: 164, 134: 162, 138:
            133, 139: 193, 140: 194, 141: 195, 142: 196, 143: 53, 144: 149,
            145: 129, 146: 130, 147: 131, 148: 132, 149: 145, 150: 146, 151:
            20, 152: 129, 153: 132, 154: 145, 155: 147, 156: 148, 157: 82,
            158: 68, 159: 83, 160: 65, 161: 36, 162: 35, 163: 81, 164: 67,
            165: 84, 166: 66, 167: 34, 168: 33, 169: 165, 170: 201,
    }
    # Floor decals that should be replaced with walls instead
    b3_floor_decal_to_wall = {
            45: 90, 50: 87, 51: 88, 56: 89, 57: 87, 62: 53, 64: 90, 65: 99,
            66: 99, 70: 100, 72: 119, 85: 88,
    }
    # Equivalent wall decal numbers to use when converting maps to B3
    b3_wall_decal_conversions = {
            1: 123, 2: 124, 3: 139, 4: 140, 5: 155, 6: 156, 7: 139, 8: 140,
            9: 37, 10: 39, 11: 38, 12: 40, 13: 58, 14: 57, 15: 3, 16: 5, 17:
            2, 18: 4, 19: 10, 20: 11, 21: 19, 22: 20, 23: 17, 24: 18, 25:
            45, 26: 46, 27: 21, 28: 22, 29: 23, 30: 24, 31: 54, 32: 53, 33:
            52, 34: 51, 35: 50, 36: 49, 37: 62, 38: 61, 39: 48, 40: 74, 41:
            73, 42: 13, 43: 12, 44: 27, 45: 26, 46: 35, 47: 36, 49: 55, 50:
            72, 51: 113, 52: 129, 53: 69, 55: 75, 56: 76,
    }
    # Equivalent entity numbers to use when converting maps to B3
    b3_entity_conversions = {
            1: 1, 2: 2, 3: 12, 4: 2, 5: 5, 6: 10, 7: 21, 8: 25, 9: 27,
            10: 28, 11: 35, 12: 1, 13: 4, 14: 7, 15: 41, 16: 37, 17: 42,
            18: 18, 19: 29, 20: 13, 21: 6, 22: 38, 23: 35,
    }
    b3_tilecontent_conversions = {
            0: 0, 1: 1, 2: 1, 3: 1, 4: 1, 5: 5, 6: 6, 7: 7, 9: 9, 10: 10,
            11: 11, 12: 13, 13: 12, 14: 14, 15: 15, 25: 25, 30: 30,
            31: 31, 32: 32, 33: 34, 34: 36, 35: 37, 37: 39, 38: 40,
    }
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

    itemincrtable = {
            0x01: 'Resist Elements',
            0x02: 'Resist Toxins',
            0x03: 'Resist Magick',
            0x04: 'Resist Disease'
        }

    flagstable = {
            0x03: 'Poisoned'
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
    categorytable = {
            0x00: '(none)',
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
            0x0E: '(Explosive?)',
            # 0x0E: Duration field displayed as "Charges" - dynamite of some sort
            0x0F: 'Potion',
            0x10: 'Reagent',
            0x11: 'Reactant',
            0x12: 'Miscellaneous',
            0x13: 'Lock Pick',
            0x14: 'Gem',
            0x15: '(unknown - n/a)',
            0x16: 'Consumable',
            0x17: 'Gold',
            0x18: 'n/a',
            0x19: 'Special',
            0x1A: 'Key'
            # Not sure if there's anything beyond here...
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

    # Should maybe just have a Spell class for this instead
    spelltype = {}
    for spell in spelltable.keys():
        if (spell < 21):
            spelltype[spell] = 'DI'
        else:
            spelltype[spell] = 'EL'

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

    # Right now this is the only one that appears to exist
    tilecontentflags = {
            0x40: 'destructible'
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

    tilecontenttypetable = {
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
            12: 'Area Event (triggered by proximity)',
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
        def __init__(self, name, health, gfxfile, friendly, movement):
            self.name = name
            self.health = health
            self.gfxfile = gfxfile
            self.friendly = friendly
            self.movement = movement

    # Entities
    entitytable = {

            # Enemies
            0x01: EntHelper('Fanged Salamander', 9, 1, 0, 1),
            0x02: EntHelper('Bloodsipper', 17, 2, 0, 1),
            0x03: EntHelper('Raptor', 95, 3, 0, 1),
            0x04: EntHelper('Noximander', 35, 4, 0, 1),
            0x05: EntHelper('Fungal Slime', 25, 5, 0, 1),
            0x06: EntHelper('Walking Corpse', 55, 6, 0, 1),
            0x07: EntHelper('Acid Grubb', 70, 7, 0, 1),
            0x08: EntHelper('Timberland Giant', 140, 8, 0, 1),
            0x09: EntHelper('Goblin Hacker', 38, 9, 0, 1),
            0x0A: EntHelper('Goblin Archer', 45, 10, 0, 1),
            0x0B: EntHelper('Goblin Warlord', 75, 11, 0, 1),
            0x0C: EntHelper('Hive Drone', 40, 12, 0, 1),
            0x0D: EntHelper('Hive Queen', 100, 13, 0, 1),
            0x0E: EntHelper('Thug', 40, 14, 0, 1),
            0x0F: EntHelper('Dimensional Eye', 80, 15, 0, 1),
            0x10: EntHelper('Giant Arachnid', 70, 16, 0, 1),
            0x11: EntHelper('Dirachnid', 250, 17, 0, 1),
            0x12: EntHelper('Skeleton', 50, 18, 0, 1),
            0x13: EntHelper('Goblin Bombthug', 15, 19, 0, 1),
            0x14: EntHelper('Poltergeist', 60, 20, 0, 1),
            0x15: EntHelper('Barrea Mercenary', 90, 21, 0, 1),
            0x16: EntHelper('Taurax', 140, 22, 0, 1),
            0x17: EntHelper('Spire Guard', 300, 60, 0, 1),

            # NPCs
            0x33: EntHelper('Maddock', 15, 51, 1, 1),
            0x34: EntHelper('Michael', 36, 52, 1, 1),
            0x35: EntHelper('Farwick', 50, 53, 1, 1),
            0x36: EntHelper('Abygale', 25, 62, 1, 1),
            0x37: EntHelper('Eleanor *', 1, 55, 1, 2),
            0x38: EntHelper('Garrett *', 1, 50, 1, 2),
            0x39: EntHelper('Porter', 32, 56, 1, 1),
            0x3A: EntHelper('Oswell *', 1, 58, 1, 2),
            0x3B: EntHelper('Lilith', 130, 54, 1, 1),
            0x3C: EntHelper('Town Guard', 120, 60, 1, 1),
            0x3D: EntHelper('Gruzz', 16, 9, 1, 1),
            0x3E: EntHelper('Gatekeeper', 45, 60, 1, 1),
            0x3F: EntHelper('Eeru', 50, 65, 1, 1),
            0x40: EntHelper('Erik', 45, 53, 1, 1),
            0x41: EntHelper('Darkford Guard', 120, 60, 1, 1),
            0x42: EntHelper('Gunther', 85, 53, 1, 1),
            0x43: EntHelper('Leurik', 22, 65, 1, 1),
            0x44: EntHelper('Vault Master', 5, 9, 1, 1),
            0x45: EntHelper('Paul', 15, 51, 1, 1),
            0x46: EntHelper('Krista', 70, 57, 1, 1),
            0x47: EntHelper('Gamfari', 20, 64, 1, 1),
            0x48: EntHelper('Larrus *', 1, 66, 1, 2),
            0x49: EntHelper('Mary', 2, 63, 1, 1),
            0x4A: EntHelper('Vekkar *', 1, 67, 1, 2),
            0x4B: EntHelper('Jonathon', 36, 52, 1, 1),
            0x4C: EntHelper('Shady Character (1)', 90, 14, 1, 1),
            0x4D: EntHelper('Oolaseph *', 1, 54, 1, 2),
            0x4E: EntHelper('Vault Guard', 50, 60, 1, 1),
            0x4F: EntHelper('Vidar the Knife', 50, 14, 1, 1),
            0x50: EntHelper('Walter', 15, 68, 1, 1),
            0x51: EntHelper('Azure Guard', 120, 60, 1, 1),
            0x52: EntHelper('Captain Morgan', 120, 60, 1, 1),
            0x53: EntHelper('Erubor', 80, 69, 1, 1),
            0x54: EntHelper('Shadowmirk Acolyte', 15, 68, 1, 1),
            0x55: EntHelper('Phillip', 15, 65, 1, 1),
            0x56: EntHelper('Omar', 140, 8, 1, 1),
            0x57: EntHelper('Gramuk', 45, 70, 1, 1),
            0x58: EntHelper('Shady Character (2)', 110, 14, 1, 1),
            0x5A: EntHelper('Chancellor Malcolm *', 4, 71, 1, 2),
            0x5B: EntHelper('Sonya', 160, 59, 1, 1),
            0x5C: EntHelper('Aaron', 70, 61, 1, 1),
            0x5D: EntHelper('Penelope', 2, 62, 1, 1),
            0x5E: EntHelper('Siam', 80, 65, 1, 1),
            0x5F: EntHelper('William', 60, 51, 1, 1),
            0x60: EntHelper('Hesham', 60, 65, 1, 1)
        }

    # Script Commands
    commands = {
            'quest': ['questnum', 'state'],
            'kill_quest': ['questnum'],
            'quest_step': ['questnum'],
            'condition': ['(text)', '(yes)', '(no)'],
            'cond_item': ['(itemname)'],
            'cond_quest': ['questnum', 'state'],
            'cond_not_quest': ['questnum', 'state'],
            'cond_special': ['num'],
            'cond_spot': [],
            'cond_health': [],
            'cond_mana': [],
            'cond_gold': ['goldamount'],
            'cond_state': ['coords', 'state'],
            'cond_detected': [],
            'give_item': ['(itemname)'],
            'remove_item': ['(itemname)'],
            'move_player': ['coords'],
            'port_to': ['coords'],
            'map': ['(mapname)'],
            'map_port': ['mapname'],
            'add_gold': ['goldamount'],
            'remove_gold': ['goldamount'],
            'heal': ['hp', 'hidden'],
            'restore': ['mp'],
            'cure_disease': ['effectiveness'],
            'cure_poison': ['val'],
            'trauma': ['hp'],
            'disease': ['diseasenum'],
            'effect': ['(effect)', 'levelnum'],
            'close_door': ['coords'],
            'close_port': ['coords'],
            'toggle_port': ['coords'],
            'toggle_obj': ['coords'],
            'destroy_obj': ['coords'],
            'drop_ent': ['entnum', 'coords'],
            'remove_npc': ['entnum'],
            'npc_die': ['entnum'],
            'npc_disp_change': ['entnum', 'disposition'],
            'trigger_talk': ['entnum'],
            'convert_tile': ['typenum'],
            'areacheck': [],
            'det_keg': ['coords'],
            'gfx': ['(gfx)', 'coords', 'colornum'],
            'message': ['(text)'],
            'narrative': ['num'],
            'kill_narrative': ['num'],
            'notebox': ['num'],
            'activate_qt': ['num'],
            'book': ['num'],
            'destroy_script': [],
            'commit_crime': [],
            'no_crime': [],
            'drama': [],
            'alert_npcs': [],
            'sound': ['(soundname)'],
            'display': ['(graphicfile)'],
            'time': [],
            'drop_item': ['(itemname)', 'percent_chance'],
            'drop_loot': [],
            'learn_book': ['booknum'],
            'learn': [],
            'remove': [],
            'to_flask': [],
            'unlocked_with': ['(keyname)'],
            'toggle_switch': [],
            'screen_fade_in': [],
            'screen_fade_out': [],
            'updatezones': [],
            'strip_items': [],
            'all_quests': [],
            'cleric_heal': [],
            'cleric_dehex': [],
            'convert': ['param'],
            'curse': [],
            'delay': ['turns'],
            'full_restore': [],
            'init_trade': ['name'],
            'poison': ['hp'],
            'remove_barrier': ['coords'],
            'rename_item': ['(old name)', '(new name)'],
            'rent_room': ['cost', 'coords'],
            'teach_skill': ['(name)', 'skillnum'],
            'trap': ['param'],
            'spell': ['(name)', 'level'],
        }

