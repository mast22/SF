# License: Public Domain
# Authors: Felix Schwarz <felix.schwarz@oss.schwarz.eu>
#
# Version 1.0

# 1.0 (06.02.2010)
#   - initial release

import unittest

__all__ = ['AttrDict']


class AttrDict(dict):
    def __getattr__(self, name):
        if name not in self:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self[name]


class AttributDictTests(unittest.TestCase):

    def test_can_use_class_as_dict(self):
        obj = AttrDict(foo=1, bar=2)
        self.assertEqual(1, obj['foo'])
        self.assertEqual(2, obj['bar'])

    def test_can_access_items_as_attributes(self):
        obj = AttrDict(foo=1, bar=2)
        self.assertEqual(1, obj.foo)
        self.assertEqual(2, obj.bar)

    def test_raise_attribute_error_for_non_existent_keys(self):
        obj = AttrDict(foo=1)
        self.assertRaises(AttributeError, getattr, obj, 'invalid')
