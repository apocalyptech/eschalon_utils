# coding=utf-8


def cmp(x, y) -> int:
    """
    Replacement for built-in funciton cmp that was removed in Python 3

    Compare the two objects x and y and return an integer according to
    the outcome. The return value is negative if x < y, zero if x == y
    and strictly positive if x > y.
    """

    return (x > y) - (x < y)
