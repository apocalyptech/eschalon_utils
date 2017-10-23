

import unittest
from struct import pack

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

    @unittest.skip("this test can cause testfile corruption - rewrite")
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
        self.assertFalse(s.eof())
        self.assertEquals(fn_to_read(s), value_to_expect_on_read)
        self.assertTrue(s.eof())

    def _test_packed_write_and_read(self,
                                    value,
                                    pack_string,
                                    fn_to_write,
                                    fn_to_read,
                                    ):
        self._test_write_and_read(
            value_to_write=value,
            raw_value_to_expect_on_read=pack(pack_string, value),
            value_to_expect_on_read=value,
            fn_to_write=fn_to_write,
            fn_to_read=fn_to_read,
        )

    def test_write_str(self):
        self._test_write_and_read(
            value_to_write="yellow".encode("ascii"),
            raw_value_to_expect_on_read=b"yellow\r\n",
            value_to_expect_on_read=b"yellow",
            fn_to_write=eschalon.savefile.Savefile.writestr,
            fn_to_read=eschalon.savefile.Savefile.readstr,
        )

    def test_write_float(self):
        self._test_packed_write_and_read(
            value=1.5,
            pack_string='f',
            fn_to_write=eschalon.savefile.Savefile.writefloat,
            fn_to_read=eschalon.savefile.Savefile.readfloat,
        )

    def test_write_double(self):
        self._test_packed_write_and_read(
            value=2.5,
            pack_string='d',
            fn_to_write=eschalon.savefile.Savefile.writedouble,
            fn_to_read=eschalon.savefile.Savefile.readdouble,
        )

    def test_write_int(self):
        self._test_packed_write_and_read(
            value=1,
            pack_string='<I',
            fn_to_write=eschalon.savefile.Savefile.writeint,
            fn_to_read=eschalon.savefile.Savefile.readint,
        )

    def test_write_signed_int(self):
        self._test_packed_write_and_read(
            value=-3,
            pack_string='<i',
            fn_to_write=eschalon.savefile.Savefile.writesint,
            fn_to_read=eschalon.savefile.Savefile.readsint,
        )

    def test_write_signed_short(self):
        self._test_packed_write_and_read(
            value=3,
            pack_string='<H',
            fn_to_write=eschalon.savefile.Savefile.writeshort,
            fn_to_read=eschalon.savefile.Savefile.readshort,
        )

    def test_write_uchar(self):
        self._test_packed_write_and_read(
            value=1,
            pack_string='B',
            fn_to_write=eschalon.savefile.Savefile.writeuchar,
            fn_to_read=eschalon.savefile.Savefile.readuchar,
        )


if __name__ == '__main__':
    unittest.main()
