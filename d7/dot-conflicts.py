#!/usr/bin/env python

import os

class ConflictsParser(object):
    """
    Checks the output produced by CheckopsParser for overlapping hunks. And
    produces a graphviz file indicating the interdependencies between issues.
    """

    def __init__(self):
        self.curnodes = set()

        self.allnodes = set()
        self.alledges = set()

    def process(self, line, filename):
        # (blob, offset, mark, length, path) = fields
        fields = line.split(" ", 5)

        if len(fields) == 5:
            issuenr = os.path.dirname(fields[4])
            self.curnodes.add(issuenr)
        else:
            self.allnodes.update(self.curnodes)

            prev = int(self.curnodes.pop())
            for node in self.curnodes:
                node = int(node)
                if (prev < node):
                    self.alledges.add((prev, node))
                else:
                    self.alledges.add((node, prev))
                prev = node


            self.curnodes = set()

    def printdot(self):
        print 'graph "Found %d overlaps between %d patches" {' % (len(self.alledges), len(self.allnodes))
        print 'rankdir=LR'
        for node in self.allnodes:
            print '%s [URL = "http://drupal.org/node/%s"]' % (node, node)
        for edge in self.alledges:
            print '%s -- %s' % edge
        print '}'

if __name__ == "__main__":
    import fileinput
    import sys

    parser = ConflictsParser()

    for line in fileinput.input():
        parser.process(line, fileinput.filename())

    parser.printdot()
