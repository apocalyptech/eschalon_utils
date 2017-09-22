import unittest

import eschalon.item

class CharacterTests(unittest.TestCase):

    def test_item_init_default(self):
        i = eschalon.item.Item()
        self.assertEquals(i.category, -1)
        i = eschalon.item.Item(zero=False)
        self.assertEquals(i.category, -1)


    def test_item_init_zero(self):
        i = eschalon.item.Item(zero=True)
        self.assertEquals(i.category, 0)


if __name__ == '__main__':
    unittest.main()
