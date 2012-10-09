import unittest

from gitpp.bom import BOMAssembler
from gitpp.segment import SegmentAssembler

class SegmentAssemblerTest(unittest.TestCase):

    def setUp(self):
        self.assembler = SegmentAssembler()
        pass

    def testEmptyHistory(self):
        segments = self.assembler.getSegments()
        self.assertEqual(segments, [])

    def testLinearHistory(self):
        """
        Test linear history: c - b - a
        """
        asm = self.assembler

        asm.startCommit()
        asm.setCommitId('a')
        asm.setParents(['b'])
        asm.endCommit()

        asm.startCommit()
        asm.setCommitId('b')
        asm.setChildren(['a'])
        asm.setParents(['c'])
        asm.endCommit()

        asm.startCommit()
        asm.setCommitId('c')
        asm.setChildren(['b'])
        asm.endCommit()

        segments = asm.getSegments()
        self.assertEqual(segments, [['a', 'b', 'c']])

    def testSimpleBranch(self):
        """
              a
             /
        c - b - b2 - b1

        Expect:
        * a
        * b - c
        * b1 - b2
        """

        asm = self.assembler

        # a
        asm.startCommit()
        asm.setCommitId('a')
        asm.setParents(['b'])
        asm.endCommit()

        # b
        asm.startCommit()
        asm.setCommitId('b')
        asm.setChildren(['a', 'b2'])
        asm.setParents(['c'])
        asm.endCommit()

        # b1
        asm.startCommit()
        asm.setCommitId('b1')
        asm.setParents(['b2'])
        asm.endCommit()

        # b2
        asm.startCommit()
        asm.setCommitId('b2')
        asm.setChildren(['b1'])
        asm.setParents(['b'])
        asm.endCommit()

        # c
        asm.startCommit()
        asm.setCommitId('c')
        asm.setChildren(['b'])
        asm.endCommit()

        segments = asm.getSegments()
        self.assertEqual(segments, [['a'], ['b', 'c'], ['b1', 'b2']])


    def testSimpleMerge(self):
        """
              a - a2 - a1
             /   /
        c - b - b2 - b1

        Expect:
        * a1 - a2
        * a
        * b - c
        * b1 - b2
        """

        asm = self.assembler

        # a1
        asm.startCommit()
        asm.setCommitId('a1')
        asm.setParents(['a2'])
        asm.endCommit()

        # a2
        asm.startCommit()
        asm.setCommitId('a2')
        asm.setChildren(['a1'])
        asm.setParents(['a', 'b2'])
        asm.endCommit()

        # a
        asm.startCommit()
        asm.setCommitId('a')
        asm.setChildren(['a1'])
        asm.setParents(['b'])
        asm.endCommit()

        # b
        asm.startCommit()
        asm.setCommitId('b')
        asm.setChildren(['a', 'b2'])
        asm.setParents(['c'])
        asm.endCommit()

        # b1
        asm.startCommit()
        asm.setCommitId('b1')
        asm.setParents(['b2'])
        asm.endCommit()

        # b2
        asm.startCommit()
        asm.setCommitId('b2')
        asm.setChildren(['b1'])
        asm.setParents(['b'])
        asm.endCommit()

        # c
        asm.startCommit()
        asm.setCommitId('c')
        asm.setChildren(['b'])
        asm.endCommit()

        segments = asm.getSegments()
        self.assertEqual(segments, [['a1', 'a2'], ['a'], ['b', 'c'], ['b1', 'b2']])


if __name__ == '__main__':
    unittest.main()
