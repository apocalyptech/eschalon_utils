import unittest

from eschalon.main import parse_args
from parameterized import parameterized


class MainTest(unittest.TestCase):
    @parameterized.expand([
        ["--book", "2", "--char"],
        ["--book", "2", "--reset-hunger", "--", "filename"],
    ])
    def test_valid_args(self, *tuple_args):
        largs = list(tuple_args)
        parse_args(largs)

    @parameterized.expand([
        ["--book", "4"],
        ["--book", "2", "--reset-hunger"],
        ["--book 2"],
    ])
    def test_invalid_args(self, *tuple_args):
        largs = list(tuple_args)
        with self.assertRaises(SystemExit):
            parse_args(largs)


if __name__ == '__main__':
    unittest.main()
