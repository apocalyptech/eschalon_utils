from eschalon.constantsb1 import B1Constants
from eschalon.constantsb2 import B2Constants
from eschalon.constantsb3 import B3Constants


class Constants(object):
    """
    A class to hold our constants, depending on what book we're
    currently working in.  I suppose really this should just modify
    a global var and set it to B1Constants or B2Constants, but
    I'll just leave it this way for now.
    """

    def __init__(self, book=1):
        assert book is not None
        self.groups = {
            1: B1Constants,
            2: B2Constants,
            3: B3Constants,
        }
        self.book = None
        self.eschalondata = None
        self.switch_to_book(book)

    def set_eschalondata(self, eschalondata):
        """
        Sets our internal EschalonData object.  Mostly just a convenience
        so that we don't have to pass that around to all the components
        which might need access to the datapak/datadir.
        """
        self.eschalondata = eschalondata

    def switch_to_book(self, book):
        assert book is not None
        if book != self.book:
            # First clear out the old constants
            if self.book:
                for (key, val) in list(self.groups[self.book].__dict__.items()):
                    if key[0] != '_':
                        del (self.__dict__[key])
            # ... and now load in the new ones
            for (key, val) in list(self.groups[book].__dict__.items()):
                if key[0] != '_':
                    self.__dict__[key] = val
            self.book = book
