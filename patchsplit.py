#!/usr/bin/env python

import re
import sys

class Patchsplit(object):
    """
    Extract hunks from patchfiles and create one new file per hunk.
    """

    # Regex for matching a hunk
    phunk = re.compile(r'^@@ -(\d+)(,(\d+))?')

    def __init__(self):
        self.spool = 0;
        self.hunk = '';
        self.filehead = '';
        self.outfile = None;
        self.filecount = 0;

    def process(self, line, filename):
        """
        Process one input line (including line terminator).
        """

        if self.spool > 0:
            self.outfile.write(line)
            if not line.startswith('+'):
                self.spool = self.spool - 1

        elif line.startswith('--- '):
            self.filehead = line

        elif line.startswith('+++ '):
            self.filehead = self.filehead + line

        else:
            result = self.phunk.match(line)
            if result:
                # FIXME: close old file, open new file
                if self.outfile:
                    self.outfile.close()

                self.filecount = self.filecount + 1

                self.outfile = open("%0.7x.diff" % self.filecount, 'w')

                self.outfile.write(self.filehead)
                self.outfile.write(line)

                # Start spooling lines following the hunk header
                if result.group(3) == None:
                    self.spool = 1
                else:
                    self.spool = int(result.group(3))
            else:
                # Ignore lines outside of hunk
                pass

if __name__ == "__main__":
    import fileinput
    parser = Patchsplit()

    for line in fileinput.input():
        parser.process(line, fileinput.filename())
