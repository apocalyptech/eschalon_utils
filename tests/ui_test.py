import unittest
import xmlunittest


class MainUITestCase(xmlunittest.XmlTestCase):

    def setUp(self):
        with open("data/maingui.ui") as df:
            self.doc = df.read()

    def test_(self):
        self.assertXmlDocument(self.doc)
        # self.assertXpathsOnlyOne()
