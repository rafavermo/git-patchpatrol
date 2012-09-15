#!/usr/bin/env python

class FailBuffer(object):
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
                print "--"

            print self.prebuf.rstrip()
            print self.failbuf.rstrip()

            self.failbuf = ''
            self.first = False

        # Clear prebuf always, even more so if no failure was reported. In this
        # case a line marked suspicous is confirmed to be innocent.
        self.prebuf = ''

class CheckopsParser(object):
    def __init__(self, failbuffer):
        self.failbuffer = failbuffer
        self.check = self.checkbegin
        self.status = 0
        self.prev = None

    def process(self, line, filename):
        fields = line.split(" ", 5)

        # Convert hex values offset and length to integer
        fields[1] = int(fields[1], 16)
        fields[3] = int(fields[3], 16)

        self.check(fields, line, filename)
        self.prev = fields

    def checkbegin(self, fields, line, filename):
        # (blob, offset, mark, length, path) = fields
        mark = fields[2]

        if mark == 'b':
            self.failbuffer.flush()
            self.failbuffer.suspect(line)
            self.check = self.checkend
        else:
            self.failbuffer.fail(line)
            self.status = 1
            self.check = self.checkbegin

    def checkend(self, fields, line, filename):
        # (blob, offset, mark, length, path) = fields
        expect = [
            self.prev[0],
            self.prev[1] + self.prev[3],
            'e',
            self.prev[3],
            self.prev[4]
        ]

        if fields == expect:
            self.failbuffer.flush()
            self.check = self.checkbegin
        else:
            self.failbuffer.fail(line)
            self.status = 1
            self.check = self.checkbegin

if __name__ == "__main__":
    import fileinput
    import sys

    failbuffer = FailBuffer()
    parser = CheckopsParser(failbuffer)

    for line in fileinput.input():
        parser.process(line, fileinput.filename())

    failbuffer.flush()
    sys.exit(parser.status)
