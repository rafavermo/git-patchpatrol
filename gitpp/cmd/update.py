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

from gitpp import patch
from gitpp.bomwalk import BOMWalk
from gitpp.cache import FilesystemResultCache
from gitpp.scm.gitcontroller import GitController


def patchid(repo, path):
    istream = open(path, 'r')
    out = repo.git.patch_id(istream=istream)
    istream.close()

    return out.split()[0]


if __name__ == '__main__':

    #logging.getLogger().setLevel(logging.DEBUG)

    bomcache = FilesystemResultCache()
    bomcache.directory = '/tmp/bomcache'
    patchcache = FilesystemResultCache()
    patchcache.directory = '/tmp/patchcache'

    repo = Repo('.')
    ctl = GitController(repo)

    patches = {}
    for patchpath in sys.argv[1:]:
        try:
            pid = patchid(repo, patchpath)
        except Exception as e:
            logging.warn('Unable to generate patchid, skipping %s' % patchpath)
            continue

        try:
            mtime = datetime.fromtimestamp(os.stat(patchpath).st_mtime)
        except Exception as e:
            logging.warn('Unable to determine mtime, skipping %s' % patchpath)
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
            logging.warn('Unable to parse patch, skipping %s' % patchpath)
            continue

        patches[pid] = p

    ctl.prepare()

    # FIXME: Setup alternative index and point GIT_INDEX_FILE to it

    segments = ctl.segmentize()
    for segment in segments:
        print "Examining segment %s..%s" % (segment[-1], segment[0])
        blobs_by_patch = {}

        if bomcache.exists(segment[0], segment[-1]):
            bom = bomcache.get(segment[0], segment[-1])
        else:
            bom = ctl.bom_from_segment(segment)
            bomcache.put(segment[0], segment[-1], bom)

        walk = BOMWalk(bom)

        for (pid, p) in patches.iteritems():
            blobs_by_patch[pid] = {}
            walk.watch(pid, p['affected'])

        for (commit, pid, paths) in walk.walk():
            blobs_by_patch[pid].update(paths)

            result = {}
            result_complete = True

            # Try to load result from cache
            for blobid in blobs_by_patch[pid].itervalues():
                if patchcache.exists(pid, blobid):
                    result[blobid] = patchcache.get(pid, blobid)
                else:
                    result_complete = False
                    break

            if not result_complete:
                logging.info('Testing patch on %s: %s' % (commit, patches[pid]['path']))
                newp = ctl.testpatch(commit, patches[pid]['path'])

                # Put result into cache for the examined blobids
                if newp == None:
                    for blobid in blobs_by_patch[pid].itervalues():
                        patchcache.put(pid, blobid, None)
                else:
                    hunks_by_blob = {}
                    currentblob = None
                    for (sym, data) in patch.parse(newp.splitlines()):
                        if sym == 'i':
                            currentblob = hunks_by_blob.setdefault(data[0], list())
                        elif sym == '@':
                            currentblob.append(data)

                    for blobid in blobs_by_patch[pid].itervalues():
                        patchcache.put(pid, blobid, hunks_by_blob[blobid])

            else:
                logging.info('Read result from cache for patch on %s: %s' % (commit, patches[pid]['path']))

    ctl.cleanup()
