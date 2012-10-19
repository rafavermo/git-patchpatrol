import hashlib
import logging
import os
import pprint
import shutil
import sys
from datetime import datetime
from git import Repo

base = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', '..'))
sys.path.append(base)

from gitpp import logger
from gitpp import patch
from gitpp.bomwalk import BOMWalk
from gitpp.cache import SimpleFSStore
from gitpp.filter.gitfilter import GitRevListFilter
from gitpp.cache import CompositeKVStore
from gitpp.scm.gitcontroller import GitController
from gitpp.segment import filter_segments
from gitpp.segmentwalk import SegmentWalk


def patchid(repo, path):
    istream = open(path, 'r')
    out = repo.git.patch_id(istream=istream)
    istream.close()

    return out.split()[0]


if __name__ == '__main__':

    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    bomcache = SimpleFSStore()
    bomcache.directory = '/tmp/bomcache'
    patchstore = SimpleFSStore()
    patchstore.directory = '/tmp/patchcache'
    patchcache = CompositeKVStore(patchstore)

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
    boms = []
    for segment in segments:
        print "Examining segment %s..%s" % (segment[-1], segment[0])
        blobs_by_patch = {}

        bomkey = (segment[0], segment[-1])
        if bomkey in bomcache:
            bom = bomcache[bomkey]
        else:
            bom = ctl.bom_from_segment(segment)
            bomcache[bomkey] = bom

        boms.append(bom)

    commit_patch_results = []
    for bom in boms:
        walk = BOMWalk(bom)

        for (pid, p) in patches.iteritems():
            blobs_by_patch[pid] = {}
            walk.watch(pid, p['affected'])

        for (commit, pid, paths) in walk.walk():
            blobs_by_patch[pid].update(paths)

            result = {}

            # Try to load result from cache
            patchkey = [(pid, blobid) for blobid in blobs_by_patch[pid].itervalues()]
            if patchkey in patchcache:
                logger.info('Read result from cache for patch on %s: %s' % (commit, patches[pid]['path']))
                result = patchcache[patchkey]
            else:
                logger.info('Testing patch on %s: %s' % (commit, patches[pid]['path']))
                newp = ctl.testpatch(commit, patches[pid]['path'])

                # Put result into cache for the examined blobids
                if newp == None:
                    result = dict((key, None) for key in patchkey)
                else:
                    hunks_by_blob = {}
                    currentblob = None
                    for (sym, data) in patch.parse(newp.splitlines()):
                        if sym == 'i':
                            currentblob = hunks_by_blob.setdefault(data[0], list())
                        elif sym == '@':
                            currentblob.append(data)
                    result = dict(((pid, blobid), hunks_by_blob[blobid]) for blobid in blobs_by_patch[pid].itervalues())

                patchcache[patchkey] = result


            commit_patch_results.append((commit, p, result))

    print len(commit_patch_results)
    ctl.cleanup()
