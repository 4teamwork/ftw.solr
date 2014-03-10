from unittest import TestCase
from ftw.solr.flare import PloneFlare


class TestPloneFlare(TestCase):

    def test_unicode_string_attribute_returned_as_byte_string(self):
        flare = PloneFlare(dict(ustring=u'Foo'))
        self.assertTrue(isinstance(flare.ustring, str))

    def test_byte_string_attribute_returned_as_byte_string(self):
        flare = PloneFlare(dict(string='Foo'))
        self.assertTrue(isinstance(flare.string, str))
