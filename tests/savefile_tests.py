from __future__ import absolute_import, unicode_literals

import unittest

import eschalon.savefile
from struct import pack


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


    def _test_write_and_read(self,
                             value_to_write,
                             raw_value_to_expect_on_read,
                             value_to_expect_on_read,
                             fn_to_write,
                             fn_to_read,
                             ):
        s = eschalon.savefile.Savefile(stringdata=b"")
        s.open_w()
        fn_to_write(s, value_to_write)
        s.df.seek(0)
        orig_content = s.df.read()
        self.assertEquals(orig_content, raw_value_to_expect_on_read)
        s.df.seek(0)
        s.df.truncate(0)
        s.df.write(orig_content)
        s = eschalon.savefile.Savefile(stringdata=orig_content)
        s.open_r()
        self.assertEquals(fn_to_read(s), value_to_expect_on_read)

    def test_write_str(self):

        self._test_write_and_read(
            value_to_write="yellow".encode("ascii"),
            raw_value_to_expect_on_read=b"yellow\r\n",
            value_to_expect_on_read=b"yellow",
            fn_to_write=eschalon.savefile.Savefile.writestr,
            fn_to_read=eschalon.savefile.Savefile.readstr,
        )

    def test_write_double(self):
        self._test_write_and_read(
            value_to_write=1.0,
            raw_value_to_expect_on_read=pack('d', 1.0),
            value_to_expect_on_read=1.0,
            fn_to_write=eschalon.savefile.Savefile.writedouble,
            fn_to_read=eschalon.savefile.Savefile.readdouble,
        )


if __name__ == '__main__':
    unittest.main()
