import unittest

from eschalon.main import parse_args
from parameterized import parameterized


class MainTest(unittest.TestCase):
    @parameterized.expand([
        [],
        ["--book", "2"],
        ["--book", "2", "--char"],
        ["--book", "2", "--reset-hunger", "--", "filename"],
    ])
    def test_valid_args(self, *args):
        parse_args(list(args))

    @parameterized.expand([
        ["--book", "4", "--char"],
        ["--book", "2", "--reset-hunger"],
        ["--book", "2", "filename"],
        ["filename"],
        ["filename", "--char", "--reset-hunger"],
    ])
    def test_invalid_args(self, *args):
        with self.assertRaises(SystemExit):
            parse_args(list(args))

    def test_default_to_char(self):
        args = parse_args(["--book", "2"])
        self.assertTrue(args.char)


if __name__ == '__main__':
    unittest.main()
