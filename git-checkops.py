#!/usr/bin/env python

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

class CheckopsParser(object):
    """
    Checks the output produced by PatchopParser for overlapping hunks. Whenever
    overlapping hunks are encountered, they are printed to stdout. Multiple
    occurences are sepparated by an empty line.
    """

    def __init__(self, failbuffer):
        self.failbuffer = failbuffer
        self.status = 0
        self.expect = []

    def process(self, line, filename):
        fields = line.split(" ", 5)

        # Convert hex values offset and length to integer
        fields[1] = int(fields[1], 16)
        fields[3] = int(fields[3], 16)

        mark = fields[2]

        if mark == 'b':
            end = [
                fields[0],
                fields[1] + fields[3],
                'e',
                fields[3],
                fields[4]
            ]
            self.expect.append(end)

            if len(self.expect) == 1:
                self.failbuffer.suspect(line)
            else:
                self.status = 1
                self.failbuffer.fail(line)

        elif mark == 'e':
            try:
                index = self.expect.index(fields)
                self.expect.pop(index)
            except ValueError as e:
                raise Error("List of operations is inconsistent. Encountered an hunk-end without having seen a matching hunk-begin.")

            if len(self.expect) == 0:
                self.failbuffer.suspect(line)
            else:
                self.status = 1
                self.failbuffer.fail(line)

        if len(self.expect) == 0:
            self.failbuffer.flush()

if __name__ == "__main__":
    import fileinput
    import sys

    failbuffer = FailBuffer()
    parser = CheckopsParser(failbuffer)

    for line in fileinput.input():
        parser.process(line, fileinput.filename())

    failbuffer.flush()
    sys.exit(parser.status)
