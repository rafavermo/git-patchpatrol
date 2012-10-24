import hashlib
import logging
import os
import shutil
import sys
from datetime import datetime
from git import Repo

base = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', '..'))
sys.path.append(base)

from gitpp import logger
from gitpp import patch
from gitpp.bomwalk import BOMWalk
from gitpp.cache import CompositeKVStore
from gitpp.cache import SimpleFSStore
from gitpp.filter.gitfilter import GitRevListFilter
from gitpp.kvbulk import KVBulkNaive
from gitpp.objectstore import ObjectStore
from gitpp.scm.gitcontroller import GitController
from gitpp.segment import filter_segments
from gitpp.segmentwalk import SegmentWalk


def patchid(repo, path):
    istream = open(path, 'r')
    out = repo.git.patch_id(istream=istream)
    istream.close()

    return out.split()[0]


def segmentid(segment):
    return "%s-%s" % (segment[-1], segment[0])


class BOMConstructionFactory(object):
    def __init__(self, ctl, segmentmap):
        self._ctl = ctl
        self._segmentmap = segmentmap

    def create(self, sids):
        result = {}

        for sid in sids:
            logger.debug('Constructing bom from segment: %s', sid)
            result[sid] = self._ctl.bom_from_segment(self._segmentmap[sid])

        return result


class PatchTestingFactory(object):
    def __init__(self, ctl, patchplan, patches):
        self._ctl = ctl
        self._patchplan = patchplan
        self._patches = patches

    def create(self, patchkeys):
        result = {}

        for patchkey in patchkeys:
            pid = patchkey[0][0]
            p = self._patches[pid]
            commit = self._patchplan[patchkey]

            logger.debug('Testing patch on %s: %s' % (commit, p['path']))

            newp = ctl.testpatch(commit, p['path'])

            # Put result into cache for the examined blobids
            if newp == None:
                result[patchkey] = dict((key, None) for key in patchkey)
            else:
                hunks_by_blob = {}
                currentblob = None
                for (sym, data) in patch.parse(newp.splitlines()):
                    if sym == 'i':
                        currentblob = hunks_by_blob.setdefault(data[0], [])
                    elif sym == '@':
                        currentblob.append(data)
                result[patchkey] = dict(((pid, blobid), hunks) for (blobid, hunks) in hunks_by_blob.iteritems())

        return result


def construct_patchplan(boms):
    result = {}

    for (sid, bom) in boms.iteritems():
        blobs_by_patch = {}
        walk = BOMWalk(bom)

        for (pid, p) in patches.iteritems():
            blobs_by_patch[pid] = {}
            walk.watch(pid, p['affected'])

        for (commit, pid, paths) in walk.walk():
            if not f.filter(commit):
                continue

            blobs_by_patch[pid].update(paths)

            patchkey = tuple((pid, blobid) for blobid in blobs_by_patch[pid].itervalues())
            result[patchkey] = commit

    return result


if __name__ == '__main__':

    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    bomcache = SimpleFSStore()
    bomcache.directory = '/tmp/bomcache'
    bomcache.multilevel = False
    bomcache.pfxlen = 0
    bombulk = KVBulkNaive(bomcache)

    patchcache = SimpleFSStore()
    patchcache.directory = '/tmp/patchcache'
    patchcache.multilevel = True
    patchbulk = KVBulkNaive(CompositeKVStore(patchcache))

    repo = Repo('.')
    ctl = GitController(repo)

    patches = {}
    for patchpath in sys.argv[1:]:
        try:
            pid = patchid(repo, patchpath)
        except Exception as e:
            logger.warn('Unable to generate patchid, skipping %s' % patchpath)
            continue

        try:
            mtime = datetime.fromtimestamp(os.stat(patchpath).st_mtime)
        except Exception as e:
            logger.warn('Unable to determine mtime, skipping %s' % patchpath)
            continue

        p = {
            'path': patchpath,
            'patchid': pid,
            'mtime': mtime,
            'affected': set()
        }

        try:
            for (sym, data) in patch.parse(open(patchpath, 'r')):
                if (sym == 'a'):
                    p['affected'].add(patch.pathstrip(data))
        except patch.ParseError as e:
            logger.warn('Unable to parse patch, skipping %s' % patchpath)
            continue

        patches[pid] = p

    ctl.prepare()

    # FIXME: Setup alternative index and point GIT_INDEX_FILE to it

    f = GitRevListFilter(repo, all=True, after='6 months')
    f.prepare()

    segments = filter_segments(ctl.segmentize(), [f])
    segmentmap = dict((segmentid(segment), segment) for segment in segments)
    bomfactory = BOMConstructionFactory(ctl, segmentmap)

    bomstore = ObjectStore(segmentmap.keys(), bombulk, bomfactory)
    bomstore.load()
    bomstore.dump()

    patchplan = construct_patchplan(bomstore.get_all())
    patchfactory = PatchTestingFactory(ctl, patchplan, patches)
    patchstore = ObjectStore(patchplan.keys(), patchbulk, patchfactory)
    patchstore.load()
    patchstore.dump()

    ctl.cleanup()
