import hashlib
import logging
import os
import pprint
import shutil
import sys
from datetime import datetime
from git import Repo
from git.errors import GitCommandError

base = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', '..'))
sys.path.append(base)

from gitpp import patch
from gitpp.bomwalk import BOMWalk
from gitpp.cache import FilesystemResultCache
from gitpp.scm.git import bom_from_segment
from gitpp.scm.git import segmentize


def savehead(path):
    headref = os.path.join(repo.path, 'HEAD')
    savedref = os.path.join(repo.path, 'ORIG_HEAD')

    if os.path.exists(savedref):
        raise Exception("ORIG_HEAD exists. Please cleanup your repository and try again")
        sys.exit(1)

    shutil.copy(headref, savedref)


def restorehead(path):
    headref = os.path.join(repo.path, 'HEAD')
    savedref = os.path.join(repo.path, 'ORIG_HEAD')

    if not os.path.exists(savedref):
        raise Exception("ORIG_HEAD does not exist. Unable to restore")

    shutil.copy(savedref, headref)
    os.unlink(savedref)


def sethead(repo, ref):
    headref = os.path.join(repo.path, 'HEAD')

    f = open(headref, 'w')
    f.write("%s\n" % ref)
    f.close()


def testpatch(repo, commit, p):
    repo.git.read_tree(commit)

    try:
        repo.git.apply(p['path'], cached=True)
        logging.debug("Patch applied on commit %s: %s" % (commit, p['path']))
    except GitCommandError:
        logging.debug("Patch failed for commit %s: %s" % (commit, p['path']))
        return

    sethead(repo, commit)

    # Reread the applied patch
    hunks_by_blob = {}
    currentblob = None
    newp = repo.git.diff(cached=True, full_index=True)
    for (sym, data) in patch.parse(newp.splitlines()):
        if sym == 'i':
            currentblob = hunks_by_blob.setdefault(data[0], list())
        elif sym == '@':
            currentblob.append(data)

    return hunks_by_blob


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

        for (sym, data) in patch.parse(open(patchpath, 'r')):
            if (sym == 'a'):
                p['affected'].add(patch.pathstrip(data))

        patches[pid] = p

    savehead(repo.path)

    # FIXME: Setup alternative index and point GIT_INDEX_FILE to it

    segments = segmentize(repo)
    for segment in segments:
        print "Examining segment %s..%s" % (segment[-1], segment[0])
        blobs_by_patch = {}

        if bomcache.exists(segment[0], segment[-1]):
            bom = bomcache.get(segment[0], segment[-1])
        else:
            bom = bom_from_segment(repo, segment)
            bomcache.put(segment[0], segment[-1], bom)

        walk = BOMWalk(segment, bom)

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
                result = testpatch(repo, commit, patches[pid])

                # Put result into cache for the examined blobids
                if result == None:
                    for blobid in blobs_by_patch[pid].itervalues():
                        patchcache.put(pid, blobid, None)
                else:
                    for blobid in blobs_by_patch[pid].itervalues():
                        patchcache.put(pid, blobid, result[blobid])

            else:
                logging.info('Read result from cache for patch on %s: %s' % (commit, patches[pid]['path']))

    restorehead(repo.path)
