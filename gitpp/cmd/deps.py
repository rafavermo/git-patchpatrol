import logging
import os
import sys

from collections import namedtuple

base = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', '..'))
sys.path.append(base)

from gitpp import logger
from gitpp.cache import CompositeKVStore
from gitpp.cache import SimpleFSSearch
from gitpp.cache import SimpleFSStore
from gitpp.kvbulk import KVBulkNaive
from gitpp.pairs import overlapping_pairs

class HunkEvent(namedtuple('HunkEvent', 'blobid start mark length patchid')):
    def __neg__(self):
        newmark = '?'
        if self.mark == 'b':
            newmark = 'e'
        elif self.mark == 'e':
            newmark = 'b'

        return HunkEvent(self.blobid, self.start + self.length, newmark,
                -self.length, self.patchid)

if __name__ == '__main__':

    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    patchcache = SimpleFSStore()
    patchcache.directory = '/tmp/patchcache'
    patchcache.multilevel = True

    # Note: We do not use CompositeKVStore here, because we want to retrieve
    # individual records, not the whole TestSets
    patchbulk = KVBulkNaive(patchcache)

    patchsearch = SimpleFSSearch()
    patchsearch.directory = '/tmp/patchcache'
    patchsearch.multilevel = True

    keys = patchsearch.search(('*', '*'))
    kvall = patchbulk.load(keys)

    # Generate list of events (start-hunk, end-hunk) from hunk database
    hunkevents = []
    for (key, hunks) in kvall.iteritems():
        (patchid, blobid) = key
        if not hunks:
            continue

        for hunk in hunks:
            event = HunkEvent(blobid, hunk[0], 'b', hunk[1], patchid)
            hunkevents.append(event)
            hunkevents.append(-event)

    hunkevents.sort()

    errhunks = list(overlapping_pairs(hunkevents))

    import pprint
    pprint.pprint(errhunks)
