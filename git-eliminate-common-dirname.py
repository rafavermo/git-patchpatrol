#!/usr/bin/env python

import os

class FailBuffer(object):
    """
    Accumulate lines which
    """
    def __init__(self):
        self.prebuf = ''
        self.failbuf = ''
        self.first = True

    def suspect(self, line):
        self.prebuf = "%s%s" % (self.prebuf, line)

    def fail(self, line):
        self.failbuf = "%s%s" % (self.failbuf, line)

    def flush(self):
        if len(self.failbuf) > 0:
            if not self.first:
                print

            print self.prebuf.rstrip()
            print self.failbuf.rstrip()

            self.failbuf = ''
            self.first = False

        # Clear prebuf always, even more so if no failure was reported. In this
        # case a line marked suspicous is confirmed to be innocent.
        self.prebuf = ''

class CommonDirnameParser(object):
    """
    Checks the output produced by CheckopParser for conflicting hunks where the
    patchfiles all share a common prefix and eliminate them from the output.
    """

    def __init__(self, failbuffer):
        self.failbuffer = failbuffer
        self.check = self.checkbegin
        self.status = 0
        self.prev = None

    def process(self, line, filename):
        fields = line.split(" ", 5)

        # (blob, offset, mark, length, path) = fields
        if len(fields) != 5:
            self.failbuffer.flush()
            self.check = self.checkbegin
        else:
            self.check(fields, line, filename)
        
        self.prev = fields

    def checkbegin(self, fields, line, filename):
        # (blob, offset, mark, length, path) = fields
        # nothing to do here
        self.failbuffer.suspect(line)
        self.check = self.checkcontinue

    def checkcontinue(self, fields, line, filename):

        path = os.path.dirname(fields[4])
        prevpath = os.path.dirname(self.prev[4])

        if path == prevpath:
            self.failbuffer.suspect(line)
        else:
            self.failbuffer.fail(line)
            self.status = 1

if __name__ == "__main__":
    import fileinput
    import sys

    failbuffer = FailBuffer()
    parser = CommonDirnameParser(failbuffer)

    for line in fileinput.input():
        parser.process(line, fileinput.filename())

    failbuffer.flush()
    sys.exit(parser.status)
