import unittest

from gitpp.cache import CompositeKVStore

class CompositeKVStoreTest(unittest.TestCase):

    def setUp(self):
        self.data = {'a': 1, 'b': 'foo', 'c': 'bar'}
        self.store = CompositeKVStore(self.data)


    def test_single_value(self):
        keys = ('a',)

        result = self.store[keys]
        self.assertEquals(result, {'a': 1})


    def test_single_missing_value(self):
        keys = ('non_existing',)

        self.assertRaises(KeyError, lambda a, b: a[b], self.store, keys)


    def test_multiple_values(self):
        keys = ('a', 'b')

        result = self.store[keys]
        self.assertEquals(result, {'a': 1, 'b': 'foo'})


    def test_put(self):
        keys = ('a', 'b')
        values = {'a': 2, 'b': 'baz'}

        self.store[keys] = values

        getkeys = ('a', 'b', 'c')
        result = self.store[getkeys]
        self.assertEquals(result, {'a': 2, 'b': 'baz', 'c': 'bar'})


if __name__ == '__main__':
    unittest.main()
