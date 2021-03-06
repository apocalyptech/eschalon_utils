import fnmatch
import os
import sys

import xmlunittest
from parameterized import parameterized


class MainUITestCase(xmlunittest.XmlTestCase):
    def setUp(self):
        with open("data/maingui.ui") as df:
            self.doc = df.read()


class MapUITestCase(xmlunittest.XmlTestCase):
    def setUp(self):
        with open("data/mapgui.ui") as df:
            self.doc = df.read()


class ItemTestCase(xmlunittest.XmlTestCase):
    def setUp(self):
        with open("data/itemgui.ui") as df:
            self.doc = df.read()


all_ui_files = ['data/maingui.ui',
                'data/mapgui.ui',
                'data/itemgui.ui',
                'data/preferences.ui',
                ]


class CommonUITestCase(xmlunittest.XmlTestCase):
    @parameterized.expand(all_ui_files)
    # @unittest.skipUnless(sys.version_info[0] == 2, "unicode issues, yay")
    def test_valid_doc(self, *args):
        fname = args[0]
        with open(fname) as df:
            self.assertXmlDocument(df.read())

    def test_all_ui_files_tested(self):
        matches = []
        for root, _, files in os.walk("data/"):
            for fname in fnmatch.filter(files, '*.ui'):
                matches.append(os.path.join(root, fname))
        if sys.version_info[0] == 2:
            self.assertItemsEqual(matches, all_ui_files)
        else:
            self.assertCountEqual(matches, all_ui_files)
