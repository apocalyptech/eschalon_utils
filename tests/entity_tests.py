import unittest

import eschalon.entity


class EntityTests(unittest.TestCase):

    def test_entity_init_default(self):
        i = eschalon.entity.Entity()
        self.assertEquals(i.x, -1)


if __name__ == '__main__':
    unittest.main()
