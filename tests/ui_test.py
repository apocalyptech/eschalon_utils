
import xmlunittest

class MainUITestCase(xmlunittest.XmlTestCase):

    def setUp(self):
        with open("data/maingui.ui") as df:
            self.doc = df.read()

    def test_valid_doc(self):
        self.assertXmlDocument(self.doc)


class MapUITestCase(xmlunittest.XmlTestCase):
    def setUp(self):
        with open("data/mapgui.ui") as df:
            self.doc = df.read()

    def test_valid_doc(self):
        self.assertXmlDocument(self.doc)
