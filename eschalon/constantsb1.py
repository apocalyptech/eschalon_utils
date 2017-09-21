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

__all__ = ['B1Constants']


class B1Constants(object):

    book = 1

    maps = [
        '14_basement',
        '14',
        '15',
        '22',
        '23',
        '24',
        '25_basement',
        '25_crypt',
        '25',
        '32',
        '33',
        '34_cave',
        '34',
        '35_cellar',
        '35_L2',
        '35',
        '41',
        '42',
        '43',
        '44',
        '45',
        '51',
        '52',
        '53',
        'bs',
        'darkford',
        'gloomful',
        'goblin_cit_l1',
        'goblin_cit_l2',
        'grimmhold_maint',
        'grimmhold',
        'lh_l2',
        'lh_l3',
        'lighthouse',
        'myst',
        'outpost',
        'shadowmirk_l1',
        'shadowmirk_l2',
        'shadowmirk_l3',
        'sinkhole',
        'to',
        'ug_reposit'
    ]
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
    for spell in list(spelltable.keys()):
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

    # I don't think these mean anything for Book 1 - materials seem
    # reasonably hardcoded.  We'll keep the values here for compatibility
    # reasons, though.
    materials_wood = []
    materials_metal = []
    materials_fabric = []

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

    # EschalonData object
    eschalondata = None

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
