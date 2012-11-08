import unittest
from collections import namedtuple

from gitpp.pairs import overlapping_pairs, lists_of_combinations

class CustomItem(namedtuple('CustomItem', 'number')):
    def __neg__(self):
        return CustomItem(-self.number)

class CheckSequenceOfPairsTest(unittest.TestCase):

    def test_empty_sequence(self):
        result = list(overlapping_pairs([]))
        self.assertEqual([], result)

    def test_correct_sequence(self):
        result = list(overlapping_pairs([1, -1, 2, -2, -4, 4]))
        self.assertEqual([], result)

    def test_sequence_with_overlapping_pairs(self):
        result = list(overlapping_pairs([1, -1, 2, -4, 4, -2, -1, 1]))
        self.assertEqual([[2, -4, 4, -2]], result)

    def test_correct_sequence_custom_item(self):
        items = [
            CustomItem(1),
            CustomItem(-1),
            CustomItem(3),
            CustomItem(-3),
        ]

        result = list(overlapping_pairs(items))
        self.assertEqual([], result)

    def test_sequence_with_overlapping_custom_pairs(self):
        items = [
            CustomItem(3),
            CustomItem(-3),
            CustomItem(1),
            CustomItem(2),
            CustomItem(-1),
            CustomItem(-2),
            CustomItem(1),
            CustomItem(-1),
        ]

        expect = [[
            CustomItem(1),
            CustomItem(2),
            CustomItem(-1),
            CustomItem(-2),
        ]]

        result = list(overlapping_pairs(items))
        self.assertEqual(expect, result)

class ListOfCombinationsTest(unittest.TestCase):
    def test_empty_list(self):
        mapseq = []

        result = list(lists_of_combinations(mapseq, 1))
        self.assertEqual([], result)

        result = list(lists_of_combinations(mapseq, 2))
        self.assertEqual([], result)

        result = list(lists_of_combinations(mapseq, 3))
        self.assertEqual([], result)

    def test_single_key_list(self):
        mapseq = (('k1', 'v1'), ('k1', 'v2'))

        result = list(lists_of_combinations(mapseq, 1))
        self.assertEqual([[('k1', 'v1'), ('k1', 'v2')]], result)

        result = list(lists_of_combinations(mapseq, 2))
        self.assertEqual([], result)

        result = list(lists_of_combinations(mapseq, 3))
        self.assertEqual([], result)

    def test_multi_key_list(self):
        mapseq = [
            ('k1', 1),
            ('k2', 2),
            ('k1', 3),
            ('k3', 4),
            ('k2', 5),
            ('k3', 6),
            ('k1', 7)
        ]

        expect = [
            [
                ('k1', 1),
                ('k1', 3),
                ('k1', 7)
            ],
            [
                ('k2', 2),
                ('k2', 5)
            ],
            [
                ('k3', 4),
                ('k3', 6)
            ]
        ]

        result = list(lists_of_combinations(mapseq, 1))
        self.assertEqual(sorted(expect), sorted(result))

        expect = [
            [
                ('k1', 1),
                ('k2', 2),
                ('k1', 3),
                ('k2', 5),
                ('k1', 7)
            ],
            [
                ('k1', 1),
                ('k1', 3),
                ('k3', 4),
                ('k3', 6),
                ('k1', 7)
            ],
            [
                ('k2', 2),
                ('k3', 4),
                ('k2', 5),
                ('k3', 6),
            ]
        ]

        result = list(lists_of_combinations(mapseq, 2))
        self.assertEqual(sorted(expect), sorted(result))

        result = [mapseq]
        result = list(lists_of_combinations(mapseq, 3))
        self.assertEqual([mapseq], result)
#
