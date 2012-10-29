import glob
import unittest
from mock import patch_object

from gitpp.cache import CompositeKVStore
from gitpp.cache import SimpleFSSearch

class SimpleFSSearchTest(unittest.TestCase):
    def _fakeresult_single(self, *args, **kwargs):
        yield '/dev/fake/1234'
        yield '/dev/fake/2345'
        yield '/dev/fake/3456'

    def _fakeresult_single_pfx2(self, *args, **kwargs):
        yield '/dev/fake/12/34'
        yield '/dev/fake/23/45'
        yield '/dev/fake/34/56'

    def _fakeresult_multi(self, *args, **kwargs):
        yield '/dev/fake/123/4'
        yield '/dev/fake/234/5'
        yield '/dev/fake/345/6'

    def _fakeresult_multi_pfx2(self, *args, **kwargs):
        yield '/dev/fake/12/3/4'
        yield '/dev/fake/23/4/5'
        yield '/dev/fake/34/5/6'

    def setUp(self):
        self.searcher = SimpleFSSearch()
        self.searcher.directory = '/dev/fake'

    @patch_object(glob, 'iglob')
    def test_search_singlelevel(self, fakeglob):
        fakeglob.side_effect = self._fakeresult_single

        self.searcher.pfxlen = 0
        result = self.searcher.search("*")

        fakeglob.assert_called_with("/dev/fake/*")
        self.assertEqual(result, ['1234','2345','3456'])

    @patch_object(glob, 'iglob')
    def test_search_singlelevel_pfx2(self, fakeglob):
        fakeglob.side_effect = self._fakeresult_single_pfx2

        self.searcher.pfxlen = 2
        result = self.searcher.search("*")

        fakeglob.assert_called_with("/dev/fake/*/*")
        self.assertEqual(result, ['1234','2345','3456'])

    @patch_object(glob, 'iglob')
    def test_search_multilevel(self, fakeglob):
        fakeglob.side_effect = self._fakeresult_multi

        self.searcher.pfxlen = 0
        self.searcher.multilevel = True
        result = self.searcher.search(("*", "*"))

        fakeglob.assert_called_with("/dev/fake/*/*")
        self.assertEqual(result, [('123', '4'), ('234', '5'), ('345', '6')])

    @patch_object(glob, 'iglob')
    def test_search_multilevel_pfx2(self, fakeglob):
        fakeglob.side_effect = self._fakeresult_multi_pfx2

        self.searcher.pfxlen = 2
        self.searcher.multilevel = True
        result = self.searcher.search(("*", "*"))

        fakeglob.assert_called_with("/dev/fake/*/*/*")
        self.assertEqual(result, [('123', '4'), ('234', '5'), ('345', '6')])

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
