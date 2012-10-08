import os
import shlex
import shutil
from git.errors import GitCommandError

from ..bom import BOMEntry, BOMAssembler
from ..segment import SegmentAssembler
from .. import logger

_HASHREMOVE = "".zfill(40)

class GitController(object):
    def __init__(self, repo):
        self._repo = repo

    def prepare(self):
        headref = os.path.join(self._repo.path, 'HEAD')
        savedref = os.path.join(self._repo.path, 'ORIG_HEAD')

        if os.path.exists(savedref):
            raise Exception("ORIG_HEAD exists. Please cleanup your repository and try again")
            sys.exit(1)

        shutil.copy(headref, savedref)
    
    def cleanup(self):
        headref = os.path.join(self._repo.path, 'HEAD')
        savedref = os.path.join(self._repo.path, 'ORIG_HEAD')

        if not os.path.exists(savedref):
            raise Exception("ORIG_HEAD does not exist. Unable to restore")

        shutil.copy(savedref, headref)
        os.unlink(savedref)

    def segmentize(self, heads = None, exclude = None, before = None, after = None):
        asm = SegmentAssembler()

        if heads == None:
            heads = self._repo.git.for_each_ref("refs/heads", format="%(refname)").splitlines()

        if exclude == None:
            exclude = []

        exargs = map(lambda a: "^%s" % a, exclude)
        args = heads + exargs + ['--']

        out = self._repo.git.rev_list(*args, format='format:%P', children=True, full_history=True, no_abbrev=True)

        for line in out.splitlines():
            if line.startswith('commit '):
                asm.endCommit()

                hashes = line.split()
                hashes.pop(0)
                asm.startCommit()
                asm.setCommitId(hashes.pop(0))
                asm.setChildren(hashes)
            else:
                hashes = line.split()
                asm.setParents(hashes)
        
        asm.endCommit()
        return asm.getSegments()


    def bom_from_segment(self, segment):
        """
        Construct a BOM (bill of material) for a given segment
        """

        asm = BOMAssembler()

        # Initial tree at the head of the segment
        asm.startEntry()
        asm.setCommitId(segment[0])

        out = self._repo.git.ls_tree(segment[0], no_abbrev=True, r=True)
        for line in out.splitlines():
            (mode, t, sha, path) = shlex.split(line)
            asm.changeBlob(path, sha)

        asm.endEntry()

        args = [segment[0], "^%s" % segment[-1], '--']
        out = self._repo.git.log(*args, no_abbrev=True, raw=True, format="format:%H %ct")

        asm.startEntry()
        for message in out.split("\n\n"):
            if (message.strip() == ''):
                continue

            lines = message.splitlines()
            (commit, timestamp) = lines.pop(0).split()

            # Workaround: Merge-only commits (not affecting any files) sometimes
            # are separated to following commits only with one newline, instead of
            # two. In this case we just stick with the following commit id.
            while(len(lines) > 0 and lines[0][0] != ':'):
                (commit, timestamp) = lines.pop(0).split()

            # New commit sha relates to blobs added in the previous loop iteration.
            asm.setCommitId(commit)
            asm.endEntry()

            # Add blobs to new commit
            asm.startEntry()

            for line in lines:
                if (line[0] != ':'):
                    continue

                (prevmode, newmode, prevsha, newsha, op, path) = shlex.split(line[1:])
                if prevsha == _HASHREMOVE:
                    asm.removeBlob(path)
                else:
                    asm.changeBlob(path, prevsha)

        asm.setCommitId(segment[-1])
        asm.endEntry()

        return asm.getEntries()


    def _sethead(self, ref):
        headref = os.path.join(self._repo.path, 'HEAD')

        f = open(headref, 'w')
        f.write("%s\n" % ref)
        f.close()


    def testpatch(self, commit, path):
        self._repo.git.read_tree(commit)

        try:
            self._repo.git.apply(path, cached=True)
            logger.debug("Patch applied on commit %s: %s" % (commit, path))
        except GitCommandError:
            logger.debug("Patch failed for commit %s: %s" % (commit, path))
            return

        self._sethead(commit)

        # Reread and return the applied patch
        hunks_by_blob = {}
        currentblob = None
        return self._repo.git.diff(cached=True, full_index=True)


if __name__ == '__main__':
    from segmentize import segmentize
    from git import Repo
    from cache import FilesystemResultCache

    r = Repo('.')
    segments = segmentize(r)

    cache = FilesystemResultCache()
    cache.directory='/tmp/bom-cache'
    for segment in segments:
        bom = bomFromSegment(r, segment)
        cache.put(segment[0], segment[-1], bom)
