import unittest
from collections import namedtuple

from gitpp.pairs import overlapping_pairs

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
