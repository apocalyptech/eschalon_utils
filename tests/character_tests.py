import unittest

from eschalon.constants import constants
import eschalon.character
import eschalon.constantsb2
import eschalon.savefile


class CharacterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # s = eschalon.savefile.Savefile(filename="test_data/book2_atend.char")
        cls.b2c = eschalon.character.Character.load(filename="test_data/book2_atend.char", book=2)
        cls.b2c.read()
        print(cls.b2c)

    def test_character_init(self):
        c = eschalon.character.B1Character(None)
        c = eschalon.character.B2Character(None)
        c = eschalon.character.B3Character(None)

    def test_character_information(self):
        c = CharacterTests.b2c
        self.assertEqual(c.name, "Veera")
        self.assertEqual(c.origin, constants.origintable.inv["Therish"])
        self.assertEqual(c.axiom, constants.axiomtable.inv["Atheistic"])
        # char.gender
        # eschalon.constantsb2.B2Constants().gendertable.
        self.assertEqual(c.gender, 2) # Female

    def test_skill_levels(self):
        c = CharacterTests.b2c
        st = constants.skilltable
        self.assertEqual(c.skills[st.inv["Mercantile"]], 4)
        self.assertEqual(c.skills[st.inv["Cleaving Weapons"]], 10)

    def test_core_attributes(self):
        c = CharacterTests.b2c
        self.assertEqual(c.strength, 30)


if __name__ == '__main__':
    unittest.main()
