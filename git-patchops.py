#!/usr/bin/env python

import re

class PatchopsParser(object):
    """
    Parse a unified diff produced using git-diff and write a pair of lines to
    stdout marking the beginning and end of each hunk. The lines are of the
    following form:

    <bbbbbbb> <fffffff> b <ccccccc> <filename>
    <bbbbbbb> <lllllll> e <ccccccc> <filename>

    Where:
    <bbbbbbb>   -- The SHA-1 hash of the affected blob
    <fffffff>   -- First line affected by this hunk in hex
    <ccccccc>   -- Total number of lines affected by this hunk in hex
    <fffffff>   -- Last line affected by this hunk in hex
    <filename>  -- The name of the patch as given on the command line or <stdin>

    The markers 'b' and 'e' denote whether the output line marks the
    beginning and end of the hunk respectively.
    """

    # Regex for matching an index-line
    pindex = re.compile(r'^index ([0-9A-Fa-f]+)')

    # Regex for matching a hunk
    phunk = re.compile(r'^@@ -(\d+)(,(\d+))?')

    def __init__(self):
        self.blob = 'xxxxxxxx'
    
    def process(self, line, filename):
        """
        Process one input line (including line terminator).
        """

        result = self.pindex.match(line)
        if result:
            # For index-lines we just remember the SHA-1 of the blob
            self.blob = result.group(1)
            return

        result = self.phunk.match(line)
        if result:
            # For hunks we parse start and length number and then write a pair
            # of lines to stdout
            start = int(result.group(1))
            length = result.group(3)
            if length:
                length = int(length)
            else:
                length = 0
            print "%s %0.7x b %0.7x %s" % (self.blob, start, length, filename)
            print "%s %0.7x e %0.7x %s" % (self.blob, start + length, length, filename)
            return

if __name__ == "__main__":
    import fileinput
    parser = PatchopsParser()

    for line in fileinput.input():
        parser.process(line, fileinput.filename())
