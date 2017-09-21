from __future__ import absolute_import

import unittest

import eschalon.savefile


class TestSavefile(unittest.TestCase):
    def test_ensure_open_only_once(self):
        s = eschalon.savefile.Savefile(stringdata=b"")
        s.open_r()

        with self.assertRaises(IOError):
                s.open_r()

        with self.assertRaises(IOError):
                s.open_w()

    def test_ensure_only_one_datatype(self):
        eschalon.savefile.Savefile(stringdata="")
        eschalon.savefile.Savefile(filename="")
        with self.assertRaises(eschalon.savefile.LoadException):
            eschalon.savefile.Savefile(filename="", stringdata="")

    def test_stringdata_invariants(self):
        s = eschalon.savefile.Savefile(stringdata="")
        self.assertTrue(s.is_stringdata())
        self.assertTrue(s.exists())

    def test_set_filename_clears_stringdata(self):
        s = eschalon.savefile.Savefile(stringdata="")
        s.set_filename("-")
        self.assertFalse(s.is_stringdata())




if __name__ == '__main__':
    unittest.main()
