from __future__ import absolute_import, unicode_literals

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
        eschalon.savefile.Savefile(stringdata=b"")
        eschalon.savefile.Savefile(filename="")
        with self.assertRaises(eschalon.savefile.LoadException):
            eschalon.savefile.Savefile(filename="", stringdata=b"")

    def test_stringdata_invariants(self):
        s = eschalon.savefile.Savefile(stringdata=b"")
        self.assertTrue(s.is_stringdata())
        self.assertTrue(s.exists())

    def test_set_filename_clears_stringdata(self):
        s = eschalon.savefile.Savefile(stringdata=b"")
        s.set_filename("-")
        self.assertFalse(s.is_stringdata())

    def test_write_str(self):
        s = eschalon.savefile.Savefile(stringdata=b"")
        s.open_w()
        s.writestr("yellow".encode("UTF-8"))
        s.df.seek(0)
        orig_content = s.df.read()
        self.assertEquals(orig_content, b"yellow\r\n")
        s = eschalon.savefile.Savefile(stringdata=orig_content)
        s.open_r()
        new_string = s.readstr()
        self.assertEquals(new_string, b"yellow")


if __name__ == '__main__':
    unittest.main()
