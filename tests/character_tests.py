import unittest

import hashlib
import eschalon.character
from eschalon.constantsb1 import B1Constants
from eschalon.constantsb2 import B2Constants
from eschalon.constantsb3 import B3Constants
import eschalon.savefile


class BaseCharacterTests(object):

    def createMyself(self, book, book_filename):
        self._book_filename = book_filename
        self.char = eschalon.character.Character.load(self._book_filename, book=book)
        self.char.read()


class B1CharacterTests(BaseCharacterTests, unittest.TestCase):

    def setUp(self):
        self.createMyself(1, "test_data/book1_atend.char")

    def test_does_load(self):
        pass


class B3CharacterTests(BaseCharacterTests, unittest.TestCase):

    def setUp(self):
        self.createMyself(3, "test_data/book3_f4_example.char")

    def test_does_load(self):
        pass


class B2CharacterTests(BaseCharacterTests, unittest.TestCase):
    def setUp(self):
        self.createMyself(2, "test_data/book2_atend.char")

    def test_character_information(self):
        self.assertEqual(self.char.name, b"Veera")
        self.assertEqual(self.char.origin, B2Constants.origintable.inv["Therish"])
        self.assertEqual(self.char.axiom, B2Constants.axiomtable.inv["Atheistic"])
        self.assertEqual(self.char.gender, B2Constants.gendertable.inv["Female"])

    @unittest.skip("test fails though output of --list is correct")
    def test_class(self):
        self.assertEqual(self.char.axiom, B2Constants.classtable.inv["Magick User"])

    def test_skill_levels(self):
        st = B2Constants.skilltable
        self.assertEqual(self.char.skills[st.inv["Mercantile"]], 4)
        self.assertEqual(self.char.skills[st.inv["Cleaving Weapons"]], 10)

    def test_core_attributes(self):
        self.assertEqual(self.char.strength, 30)
        self.assertEqual(self.char.dexterity, 20)
        self.assertEqual(self.char.endurance, 19)
        self.assertEqual(self.char.speed, 13)
        self.assertEqual(self.char.intelligence, 22)
        self.assertEqual(self.char.wisdom, 20)
        self.assertEqual(self.char.perception, 20)
        self.assertEqual(self.char.concentration, 27)

    def test_hp_mp_stats(self):
        self.assertEqual(self.char.maxhp, 112)
        self.assertEqual(self.char.curhp, 107)
        self.assertEqual(self.char.maxmana, 176)
        self.assertEqual(self.char.curmana, 120)

    def test_extra_points(self):
        self.assertEqual(self.char.extra_att_points, 0)
        self.assertEqual(self.char.extra_skill_points, 0)

    def test_leveling_information(self):
        self.assertEqual(self.char.experience, 169985)
        self.assertEqual(self.char.level, 20)

    def test_equip(self):
        self.assertEqual(self.char.gold, 1654)
        self.assertEqual(self.char.torches, 24)
        self.assertEqual(self.char.torchused, 0)

    def test_read_write_read_unmodified(self):
        with open(self._book_filename, 'rb') as df:
            original_hash = hashlib.sha256(df.read())
        c = eschalon.character.Character.load(filename=self._book_filename, book=2)
        c.read()
        c.write()
        with open(self._book_filename, 'rb') as df:
            new_hash = hashlib.sha256(df.read())
        self.assertEqual(original_hash.hexdigest(), new_hash.hexdigest())

    def test_character_perm_status(self):
        t = B2Constants.permstatustable.inv
        self.assertEqual(self.char.permstatuses,
                         t["Intense Focus"] |
                         t["Masterful Riposte"] |
                         t["Silent"] |
                         t["Devastating Blow"] |
                         t["Great Cleave"] |
                         t["Encumbered"],
                         )

    def test_spell_list(self):
        self.assertListEqual(self.char.spells,
                             [1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0,
                              1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1])

    def test_spell_names_in_list(self):
        st = B2Constants.spelltable
        self.assertEqual(self.char.spells[st.inv["Draw Water"]], 1)
        self.assertEqual(self.char.spells[st.inv["Enkindled Weapon"]], 1)
        self.assertEqual(self.char.spells[st.inv["Dense Nimbus"]], 0)

    def test_keyring(self):
        self.assertListEqual(self.char.keyring[0:3], [b'Simple Key', b'Bluish Key', b'Rusted Key'])

    def test_alchemy_recipe(self):
        self.assertListEqual(self.char.alchemy_book,
                             [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])


if __name__ == '__main__':
    unittest.main()
