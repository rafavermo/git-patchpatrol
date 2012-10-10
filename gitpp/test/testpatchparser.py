import unittest
import os

from gitpp.patch import parse, pathstrip

class PatchParseTest(unittest.TestCase):

    def setUp(self):
        patchpath = os.path.join(os.path.dirname(__file__), 'fixtures', 'locale-module-css-cleanup.patch')
        self.patch = open(patchpath, 'r')

    def testParser(self):
        expect_index = [
            ('aaf1988', '0000000'),
            ('38112b5', '0000000'),
            ('3bb02ca', '7e4f2b6'),
            ('8e95202', '9b49da9'),
            ('58aed57', '5b3e42a'),
            ('f36fa96', 'de68a8b'),
            ('8bb8026', '1dc3d55')
        ]
        expect_oldpaths = [
            'a/modules/locale/locale-rtl.css',
            'a/modules/locale/locale.css',
            'a/themes/bartik/css/style-rtl.css',
            'a/themes/bartik/css/style.css',
            'a/themes/garland/style-rtl.css',
            'a/themes/garland/style.css',
            'a/themes/seven/style.css'
        ]
        expect_newpaths = [
            '/dev/null',
            '/dev/null',
            'b/themes/bartik/css/style-rtl.css',
            'b/themes/bartik/css/style.css',
            'b/themes/garland/style-rtl.css',
            'b/themes/garland/style.css',
            'b/themes/seven/style.css'
        ]
        expect_hunks = [
            (1,12,0,0),
            (1,32,0,0),
            (274,3,274,16),
            (1570,6,1570,35),
            (342,3,342,18),
            (1168,6,1168,35),
            (987,3,987,34)
        ]

        expect_inserts = 117
        expect_deletes = 44
        expect_context = 21
        expect_extensions = 10

        index = []
        oldpaths = []
        newpaths = []
        hunks = []

        inserts = 0
        deletes = 0
        context = 0
        extensions = 0

        for (sym, data) in parse(self.patch):
            if sym == 'i':
                index.append(data)
            elif sym == 'a':
                oldpaths.append(data)
            elif sym == 'b':
                newpaths.append(data)
            elif sym == '@':
                hunks.append(data)
            elif sym == '+':
                inserts += 1
            elif sym == '-':
                deletes += 1
            elif sym == '=':
                context += 1
            elif sym == '?':
                extensions += 1

        self.assertEqual(index, expect_index)
        self.assertEqual(oldpaths, expect_oldpaths)
        self.assertEqual(newpaths, expect_newpaths)
        self.assertEqual(hunks, expect_hunks)
        self.assertEqual(inserts, expect_inserts)
        self.assertEqual(deletes, expect_deletes)
        self.assertEqual(context, expect_context)
        self.assertEqual(extensions, expect_extensions)


    def testPathstrip(self):
        subject = '/dev/null'
        self.assertEqual(None, pathstrip(subject, 0))
        self.assertEqual(None, pathstrip(subject, 1))
        self.assertEqual(None, pathstrip(subject, 2))

        subject = 'a/modules/locale/locale-rtl.css'
        self.assertEqual(subject, pathstrip(subject, 0))
        self.assertEqual('modules/locale/locale-rtl.css', pathstrip(subject, 1))
        self.assertEqual('locale/locale-rtl.css', pathstrip(subject, 2))

if __name__ == '__main__':
    unittest.main()
