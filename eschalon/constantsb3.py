#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id: constantsb2.py,v 1.17 2010/08/03 22:23:53 pez Exp $
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2017 CJ Kucera, Elliot Kendall, Eitan Adler
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
import logging

LOG = logging.getLogger(__name__)


__all__ = ['B3Constants']


class B3Constants(object):

    book = 3

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

    skilltable = {
        0x01: 'Alchemy',
        0x02: 'Divination',
        0x03: 'Elemental',
        0x04: 'Light Armor',
        0x05: 'Heavy Armor',
        0x06: 'Shields',
        0x07: 'Cartography',
        0x08: 'Dodge',
        0x09: 'Foraging',
        0x0A: 'Hide in Shadows',
        0x0B: 'Lore',
        0x0C: 'Medicine',
        0x0D: 'Meditation',
        0x0E: 'Mercantile',
        0x0F: 'Move Silently',
        0x10: 'Pick Locks',
        0x11: 'Repair',
        0x12: 'Skullduggery',
        0x13: 'Spot Hidden',
        0x14: 'Unarmed Combat',
        0x15: 'Bludgeoning Weapons',
        0x16: 'Bows',
        0x17: 'Cleaving Weapons',
        0x18: 'Piercing Weapons',
        0x19: 'Swords',
        0x1A: 'Thrown Weapons'
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
        0x0D: 'Wand',
        0x0E: 'Spell',
        0x0F: 'Potion',
        0x10: 'Recipe',
        0x11: 'Reagent',
        0x12: 'Book',
        0x13: 'Miscellaneous',
        0x14: 'Lockpick',
        0x15: 'Gem',
        0x16: 'Torch',
        0x17: 'Consumable (food)',
        0x18: 'Consumable (waterskin)',
        0x19: 'Gold',
        0x1A: 'n/a',
        0x1B: 'Special',
        0x1C: 'Key',
        0x1D: 'Explosive'
        # Not sure if there's anything beyond here...
    }

    spelltable = {
        0: 'Draw Water',
        1: 'Element Armor',
        2: 'Spark',
        3: 'Gravedigger\'s Flame',
        4: 'Predator Sight',
        5: 'Reveal Map',
        6: 'Sonic Blast',
        7: 'Dazzling Flare',
        8: 'Firetouch',
        9: 'Dense Nimbus',
        10: 'Chameleon',
        11: 'Compress Atmosphere',
        12: 'Enkindled Weapon',
        13: 'Toxic Element',
        14: 'Polar Claw',
        15: 'Fireball',
        16: 'Lock Melt',
        17: 'Milo\'s Cell of Holding',
        18: 'Trapkill',
        19: 'Abyssal Freeze',
        20: 'Ice Lance',
        21: 'Invisibility',
        22: 'Portal',
        23: 'Supernova',
        24: 'Bless',
        25: 'Cat\'s Eyes',
        26: 'Malachai\'s Gruel',
        27: 'Detox',
        28: 'Divine Heal',
        29: 'Entangle',
        30: 'Fleshboil',
        31: 'Lore',
        32: 'Guiding Light',
        33: 'Leatherskin',
        34: 'Charm',
        35: 'Cure Ailments',
        36: 'Enchanted Weapon',
        37: 'Haste',
        38: 'Nimbleness',
        39: 'Ogre Strength',
        40: 'Protection from Curses',
        41: 'Sunder Flesh',
        42: 'Turn Undead',
        43: 'Stoneskin',
        44: 'Dehex',
        45: 'Mystic Hammer',
        46: 'Mass Boil',
        47: 'Graven Idol'
    }

    # Should maybe just have a Spell class for this instead
    spelltype = {}
    for spell in list(spelltable.keys()):
        if (spell < 24):
            spelltype[spell] = 'EL'
        else:
            spelltype[spell] = 'DI'

    statustable = {
        0: 'Chameleon',
        1: 'Protection from Curses',
        2: 'Entangled',
        3: 'Paralyzed',
        4: 'Poisoned',
        5: 'Scared',
        6: 'Stunned',
        7: 'Off-Balance',
        8: 'Dense Nimbus',
        9: 'Enchanted Weapon',
        10: 'Cat\'s Eyes',
        11: 'Gravedigger\'s Flame',
        12: 'Blessed',
        13: 'Haste',
        14: 'Ogre Strength',
        15: 'Invisible',
        16: 'Leatherskin',
        17: 'Nimbleness',
        18: 'Reveal Map',
        19: 'Stoneskin',
        20: 'Keensight',
        21: 'Enkindled Weapon',
        22: 'Elemental Armor',
        23: 'Predator Sight',
        24: 'Mana Fortified',
        25: 'Greater Protection',
        26: 'Guiding Light',
        27: 'Blind',
        28: 'Unknown 1',
        29: 'Unknown 2',
    }

    # Rather a lot of duplicated information in here, but it turns
    # out there's a "Polearm Weapons" in the middle of the table which isn't
    # present elsewhere, so it'd be harder to just populate from the existing
    # tables.  So whatever.
    itemeffecttable = {
        0x01: 'Strength',
        0x02: 'Dexterity',
        0x03: 'Endurance',
        0x04: 'Speed',
        0x05: 'Intelligence',
        0x06: 'Wisdom',
        0x07: 'Perception',
        0x08: 'Concentration',
        0x09: 'Alchemy',
        0x0A: 'Divination',
        0x0B: 'Elemental',
        0x0C: 'Light Armor',
        0x0D: 'Heavy Armor',
        0x0E: 'Shields',
        0x0F: 'Cartography',
        0x10: 'Dodge',
        0x11: 'Foraging',
        0x12: 'Hide in Shadows',
        0x13: 'Lore',
        0x14: 'Meditation',
        0x15: 'Mercantile',
        0x16: 'Move Silently',
        0x17: 'Pick Locks',
        0x18: 'Repair',
        0x19: 'Skullduggery',
        0x1A: 'Spot Hidden',
        0x1B: 'Medicine',
        0x1C: 'Unarmed Combat',
        0x1D: 'Bludgeoning Weapons',
        0x1E: 'Bows',
        0x1F: 'Cleaving Weapons',
        0x20: 'Piercing Weapons',
        0x21: '(Polearm Weapons)',
        0x22: 'Swords',
        0x23: 'Thrown Weapons',
        0x24: 'ToHit',
        0x25: 'Damage',
        0x26: 'Armor Rating',
        0x27: 'Damage Reduction',
        0x28: 'Elemental Resistance',
        0x29: 'Toxin Resistance',
        0x2A: 'Magick Resistance',
        0x2B: 'Disease Resistance',
        0x2C: 'All Resistance',
        0x2D: 'Hit Points',
        0x2E: 'Mana Points',
        0x2F: 'Hunger',
        0x30: 'Thirst',
        0x31: 'Fire Damage',
        0x32: 'Freeze Damage',
        0x33: 'Magick Damage',
        0x34: 'Poison',
        0x35: 'Small Effect Area (thrown potions)',
        0x36: 'Medium Effect Area (thrown potions)',
        0x37: 'Large Effect Area (thrown potions)',
        0x38: 'Not implemented',
        0x39: 'Radiant',
    }

    materials_wood = ['Pine',
                      'Birch',
                      'Oak',
                      'Maple',
                      'Walnut',
                      'Hickory',
                      'Mahogany',
                      'Ebony',
                      'Petrified',
                      'Diamond Grained',
                      ]

    materials_metal = ['Copper',
                       'Bronze',
                       'Iron',
                       'Steel',
                       'Tempered Steel',
                       'Dwarven Steel',
                       'Tungsten',
                       'Mithril',
                       'Adamantium',
                       'Epic Ore',
                       ]

    materials_fabric = ['Hemp',
                        'Hide',
                        'Leather',
                        'Boiled Leather',
                        'Studded Leather',
                        'Reptile Hide',
                        'Studded Reptile Hide',
                        'Dragon Skin',
                        'Spun Adamantium',
                        'Ancient Dragon Skin',
                        ]

    # This table is a bitfield lookup
    permstatustable = {
        0x00000001: '(unknown 1)',
        0x00000002: 'Broken Left Arm',
        0x00000004: 'Broken Right Arm',
        0x00000008: 'Concussion',
        0x00000010: 'Starving',
        0x00000020: 'Dehydrated',
        0x00000040: 'Cursed',
        0x00000080: 'Tapeworms',
        0x00000100: 'Deadman\'s Thirst',
        0x00000200: 'Bloodboil',
        0x00000400: 'Brain Mold',
        0x00000800: 'The Shambles',
        0x00001000: 'Unskilled Weapon Penalty',
        0x00002000: 'Unskilled Armor Penalty (light)',
        0x00004000: 'Unskilled Armor Penalty (heavy)',
        0x00008000: 'Unskilled Shield Penalty',
        0x00010000: 'Encumbered',
        0x00020000: 'Overburdened',
        0x00040000: 'Hidden in Shadow',
        0x00080000: 'Silent',
        0x00100000: 'Devastating Blow',
        0x00200000: 'Great Cleave',
        0x00400000: 'Fury Strike',
        0x00800000: 'Intense Focus',
        0x01000000: 'Masterful Riposte',
        0x02000000: 'Overwhelming Volley',
        0x04000000: 'Double Strike',
        0x08000000: '(unknown 8)',
        0x10000000: '(unknown 9)',
        0x20000000: '(unknown 10)',
        0x40000000: '(unknown 11)',
        0x80000000: '(unknown 12)'
    }

    alchemytable = {
        0: 'Cat\'s Eyes Brew',
        1: 'Detox Serum',
        2: 'Demon Oil',
        3: 'Elixir of Cure Ailment',
        4: 'Flask of Charm Cloud',
        5: 'Flask of Toxic Aura',
        6: 'Healing Elixir',
        7: 'Invisibility',
        8: 'Mana Potion',
        9: 'Potion of Fortify Mana',
        10: 'Potion of Greater Protection',
        11: 'Potion of Haste',
        12: 'Potion of Keensight',
        13: 'Potion of Leatherskin',
        14: 'Potion of Nimbleness',
        15: 'Potion of Ogre Strength',
        16: 'Potion of Predator Sight',
        17: 'Potion of Restoration',
        18: 'Potion of Stone Skin',
        19: 'Imbue ToHit',
        20: 'Imbue Damage',
        21: 'Harden Armor',
        22: 'Imbue with Fire',
        23: 'Imbue with Cold',
        24: 'Imbue with Poison',
        25: 'Create Fused Keg',
        26: 'Refill Lantern',
    }

    gendertable = {
        1: 'Male',
        2: 'Female'
    }

    origintable = {
        1: 'Nor\'lander',
        2: 'Barrean',
        3: 'Emayu',
        4: 'Therish',
        5: 'Kessian'
    }

    axiomtable = {
        1: 'Atheistic',
        2: 'Druidic',
        3: 'Virtuous',
        4: 'Nefarious',
        5: 'Agnostic'
    }

    classtable = {
        1: 'Fighter',
        2: 'Rogue',
        3: 'Magick User',
        4: 'Healer',
        5: 'Ranger'
    }

    picidtable = {
        1: 'Male #1',
        2: 'Male #2',
        3: 'Male #3',
        4: 'Male #4',
        5: 'Male #5',
        6: 'Male #6',
        7: 'Female #1',
        8: 'Female #2',
        9: 'Female #3',
        10: 'Female #4',
        11: 'Female #5',
        12: 'Female #6',
        4294967295: 'Custom'
    }

    # Right now this is the only one that appears to exist
    tilecontentflags = {
        0x40: 'destructible'
    }

    traptable = {
        0: 'none',
        1: 'Steam Bath',
        2: 'The Hobbler',
        3: 'Barbed Darts',
        4: 'Bixby\'s Noxious Cloud',
        5: 'Festering Stew',
        6: 'Thieves\' Surprise',
        7: 'Wicked Sunrise',
        8: 'Yara\'s Vengeance',
        9: 'Dragonbite',
        10: 'Sublime Armageddon'
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
        1: 'Container (no open/close change - barrels, etc)',
        2: 'Container (chests, dressers, etc)',
        3: '(broken container type, don\'t use)',
        4: 'Container (bag)',
        5: 'Door',
        6: 'Map Link',
        7: 'Clickable Action (lever, Well in Eastwillow)',
        8: 'Entrance to Thieves\' Arcadia',
        9: 'Message (wall decal - plaques, bookcases)',
        10: 'Message (wall - signs, gravestones)',
        11: 'Sealed Barrel',
        12: 'Sconce',
        13: 'Area Event (triggered by proximity)',
        14: 'Trap / Teleporter / Other tile-triggered action',
        15: 'Powder Keg',
        16: 'Well',
        17: 'Archery Target',
        18: 'Nest / Computer Teriminal',
        19: 'Zapper',
        21: 'Big Graphic',
        22: 'Breakable Wall',
        23: 'Ceramic pot (breakable with powder keg)',
        25: 'Light Source (white)',
        26: 'Light Source (red)',
        27: 'Light Source (green)',
        28: 'Light Source (blue)',
        29: 'Light Source (yellow)',
        30: 'Sound Generator (Inn)',
        31: 'Sound Generator (Church)',
        32: 'Sound Generator (Cold Wind)',
        33: 'Sound Generator (Dripping Water)',
        34: 'Sound Generator (Bubbling Water)',
        35: 'Sound Generator (River)',
        36: 'Sound Generator (Magic Shop)',
        37: 'Sound Generator (Blacksmith)',
        38: 'Sound Generator (Swamp Insects)',
        39: 'Sound Generator (Busy Street)',
        40: 'Sound Generator (Waterfall)',
        41: 'Sound Generator (Wind, with Tapping)',
        42: 'Sound Generator (Wind)',
        43: 'Sound Generator (Swimming Water)',
        44: 'Sound Generator (Electric Field)',
    }

    # EschalonData object
    eschalondata = None

    # I'm not fond of the way we're defining this class in multiple constants files
    class BigGfxHelper(object):
        def __init__(self, image, name, barrier):
            self.image = image
            self.name = name
            self.barrier = barrier

    big_gfx_list = [
        BigGfxHelper('sgfx_wagon.png', 'Wagon', 1),
        BigGfxHelper('sgfx_docked_ship_1.png', 'Docked Ship #1', None),
        BigGfxHelper('sgfx_corsair.png', 'Docked Ship #2', None),
        BigGfxHelper('sgfx_sunk_boat.png', 'Shipwreck', None),
        BigGfxHelper('sgfx_wrecked_ship_top.png', 'Wrecked Ship (top)', None),
        BigGfxHelper('sgfx_wrecked_ship_middle.png',
                     'Wrecked Ship (middle)', None),
        BigGfxHelper('sgfx_wrecked_ship_bottom.png',
                     'Wrecked Ship (bottom)', None),
        BigGfxHelper('sgfx_fishbones.png', 'Fish Skeleton', 1),
        BigGfxHelper('sgfx_dead_megafish.png', 'Megafish Skeleton', 1),
        BigGfxHelper('sgfx_father_tree_1.png', 'Ulgolek (dying)', 1),
        BigGfxHelper('sgfx_father_tree_2.png', 'Ulgolek (healed)', 1),
        BigGfxHelper('sgfx_gears.png', 'Dwarven Gears', 1),
        BigGfxHelper('sgfx_mpart1.png', 'Orakur Machinery Cube', 1),
        BigGfxHelper('sgfx_mpart2.png', 'Orakur Machinery Scraps', 1),
        BigGfxHelper('sgfx_orerry.png', 'Orrery', 1),
        BigGfxHelper('sgfx_raft.png', 'Raft', 5),
        BigGfxHelper('sgfx_rockhammer_sign.png', 'Rockhammer Sign', None),
        BigGfxHelper('sgfx_skull_entrance.png',
                     'Omentor Temple Entrance', None),
        BigGfxHelper('sgfx_swarm_nest.png', 'Swarm Nest', 1),
    ]

    # Script Commands
    commands = {
        'quest': ['questnum', 'state'],
        'kill_quest': ['questnum'],
        'quest_step': ['questnum'],
        'condition': ['(text)', '(yes)', '(no)'],
        'cond_item': ['(itemname)'],
        'cond_not_item': ['(itemname)'],
        'cond_quest': ['questnum', 'state'],
        'cond_not_quest': ['questnum', 'state'],
        'cond_special': ['num'],
        'cond_spot': [],
        'cond_touch': [],
        'cond_health': [],
        'cond_mana': [],
        'cond_gold': ['goldamount'],
        'cond_state': ['coords', 'state'],
        'cond_detected': [],
        'give_item': ['(itemname)'],
        'remove_item': ['(itemname)'],
        'move_player': ['coordss'],
        'portfx': [],
        'port_to': ['coords'],
        'map_port': ['(mapname)', 'coords'],
        'add_gold': ['goldamount'],
        'remove_gold': ['goldamount'],
        'learn_recipe': ['recipenum'],
        'gain_xp': ['xp'],
        'visit_well': [],
        'eat': ['foodval', 'drinkval'],
        'heal': ['hp', 'hidden'],
        'restore': ['mp'],
        'cure_ailment': [],
        'cure_poison': ['val'],
        'trauma': ['hp'],
        'disease': ['diseasenum'],
        'player_effect': ['effectnum', 'levelnum', 'durationnum'],
        'close_door': ['coords'],
        'open_port': ['coords'],
        'close_port': ['coords'],
        'toggle_port': ['coords'],
        'toggle_obj': ['coords'],
        'toggle_zapper': ['coords'],
        'destroy_obj': ['coords'],
        'drop_ent': ['entnum', 'coords'],
        'remove_npc': ['entnum'],
        'npc_die': ['entnum'],
        'npc_disp_change': ['entnum', 'disposition'],
        'trigger_talk': ['entnum'],
        'convert_tile': ['coords', 'typenum'],
        'areacheck': [],
        'det_keg': ['coords'],
        'special_event': ['num'],
        'gfx': ['(effect)', 'coords', 'colornum'],
        'msg': ['(text)'],
        'narrative': ['num'],
        'kill_narrative': ['num'],
        'activate_qt': ['num'],
        'book': ['num'],
        'destroy_script': [],
        'commit_crime': [],
        'no_crime': [],
        'drama': [],
        'alert_npcs': [],
        'sound': ['(soundname)'],
        'asfx': ['(soundname)', 'coords'],
        'display': ['(graphicfile)'],
        'time': [],
        'drop_gold': ['goldamount'],
        'drop_item': ['(itemname)', 'percent_chance'],
        'drop_loot': ['lootlevel'],
        'learn_skill': ['skillnum'],
        'learn_spell': [],
        'remove': [],
        'to_flask': [],
        'drink': [],
        'unlocked_with': ['(keyname)'],
        'toggle_switch': [],
        'screen_fade_in': [],
        'screen_fade_out': [],
        'updatezones': [],
        'strip_items': [],
        'all_quests': [],
        'cleric_heal': [],
        'cleric_dehex': [],
        'curse': [],
        'delay': ['turns'],
        'full_restore': [],
        'init_trade': ['entnum'],
        'poison': ['num'],
        'remove_barrier': ['coords'],
        'rename_item': ['(old name)', '(new name)'],
        'rent_room': ['cost', 'coords'],
        'teach_skill': ['(name)', 'skillnum'],
        'trap': ['param'],
        'spell': ['(name)', 'level'],
    }

    # Data
    s = '8UKI-we0IrTU_GTBclOnipmDrIUOOmk_TuaiKdHiUxs='
    d = 'mCHMjWyeZkmQ4QueVJgetB3u8KjAP2Vktw7Fvy2Devql5Yi3aAMoxtDJIGH95Huk'
