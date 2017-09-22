import unittest

import eschalon.character

class CharacterTests(unittest.TestCase):
    def test_characer_init(self):
        c = eschalon.character.B1Character(None)
        c = eschalon.character.B2Character(None)
        c = eschalon.character.B3Character(None)


if __name__ == '__main__':
    unittest.main()
