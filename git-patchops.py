#!/usr/bin/env python

import re

class PatchopsParser(object):
    pindex = re.compile(r'^index ([0-9A-Fa-f]+)')
    phunk = re.compile(r'^@@ -(\d+)(,(\d+))?')

    def __init__(self):
        self.blob = 'xxxxxxxx'
    
    def process(self, line, filename):

        result = self.pindex.match(line)
        if result:
            self.blob = result.group(1)
            return

        result = self.phunk.match(line)
        if result:
            start = int(result.group(1))
            length = result.group(3)
            if length:
                length = int(length)
            else:
                length = 0
            print "%s %0.4x b %0.4x %s" % (self.blob, start, length, filename)
            print "%s %0.4x e %0.4x %s" % (self.blob, start + length, length, filename)
            return

if __name__ == "__main__":
    import fileinput
    parser = PatchopsParser()

    for line in fileinput.input():
        parser.process(line, fileinput.filename())
