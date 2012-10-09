import unittest

from gitpp.bomwalk import BOMWalk
from gitpp.bom import BOMEntry

class BOMWalkTest(unittest.TestCase):

    def setUp(self):
        bom = [
            BOMEntry(id=4, change={'a':4, 'b': 44, 'c': 444, 'd': 4444}, remove=[]),
            BOMEntry(id=3, change={'a':3, 'c':333}, remove=[]),
            BOMEntry(id=2, change={}, remove=['b']),
            BOMEntry(id=1, change={'a':1, 'd':1111}, remove=[])
        ]
        self.walker = BOMWalk(bom)

    def testNoWatch(self):
        for (commit, key, paths) in self.walker.walk():
            self.fail('Walk should not yield if no watches are specified')

    def testWatchOne(self):
        apath = ['a']

        self.walker.watch('apath', apath)
        walkit = self.walker.walk()

        # In commit id=4, all paths have changed
        (commitid, key, paths) = walkit.next()
        self.assertEqual(commitid, 4)
        self.assertEqual(key, 'apath')
        self.assertEqual(paths, {'a':4})

        # In commit id=3, paths 'a' and 'c' have changed
        (commitid, key, paths) = walkit.next()
        self.assertEqual(commitid, 3)
        self.assertEqual(key, 'apath')
        self.assertEqual(paths, {'a':3})

        # In commit id=2 nothing changes concerning the apath-set

        # In commit id=1, paths 'a' is changed
        (commitid, key, paths) = walkit.next()
        self.assertEqual(commitid, 1)
        self.assertEqual(key, 'apath')
        self.assertEqual(paths, {'a':1})

        # Iterator should be finished here
        self.assertRaises(StopIteration, lambda it: it.next(), walkit)

    def testWatchAll(self):
        allpaths = ['a', 'b', 'c', 'd']

        self.walker.watch('allpaths', allpaths)
        walkit = self.walker.walk()

        # In commit id=4, all paths have changed
        (commitid, key, paths) = walkit.next()
        self.assertEqual(commitid, 4)
        self.assertEqual(key, 'allpaths')
        self.assertEqual(paths, {'a':4, 'b': 44, 'c': 444, 'd': 4444})

        # In commit id=3, paths 'a' and 'c' have changed
        (commitid, key, paths) = walkit.next()
        self.assertEqual(commitid, 3)
        self.assertEqual(key, 'allpaths')
        self.assertEqual(paths, {'a':3, 'c': 333})

        # In commit id=2, path 'b' is removed. Therefore the iterator will not
        # fire for commit id=1, because one of the watched paths is missing.
        self.assertRaises(StopIteration, lambda it: it.next(), walkit)

    def testWatchTwoSets(self):
        ab = ['a', 'b']
        cd = ['c', 'd']

        self.walker.watch('ab', ab)
        self.walker.watch('cd', cd)
        walkit = self.walker.walk()

        # Examine results for commitid=4
        expect = {
                (4, 'ab'): {'a': 4, 'b': 44},
                (4, 'cd'): {'c': 444, 'd': 4444}
        }
        (commitid, key, paths) = walkit.next()
        self.assertEqual(paths, expect.pop((commitid, key)))
        (commitid, key, paths) = walkit.next()
        self.assertEqual(paths, expect.pop((commitid, key)))

        # Examine results for commitid=3
        expect = {
                (3, 'ab'): {'a': 3},
                (3, 'cd'): {'c': 333}
        }
        (commitid, key, paths) = walkit.next()
        self.assertEqual(paths, expect.pop((commitid, key)))
        (commitid, key, paths) = walkit.next()
        self.assertEqual(paths, expect.pop((commitid, key)))

        # No results from commitid=2

        # Only cd-set in commitid=1
        actual = walkit.next()
        self.assertEqual(actual, (1, 'cd', {'d': 1111}))

if __name__ == '__main__':
    unittest.main()
