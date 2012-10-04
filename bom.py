import hashlib
import shlex

class BOM(object):
    def __init__(self):
        self._current_blobs = {}
        self._paths = {}

    def startCommit(self):
        self._current_blobs = {}

    def addBlob(self, path, blobid):
        pathid = hashlib.sha1(path).hexdigest()
        self._current_blobs[pathid] = blobid

    def endCommit(self, sha):
        if len(self._current_blobs) < 1:
            return

        for (pathid, blobid) in self._current_blobs.iteritems():
            blobs = self._paths.setdefault(pathid, {})
            blobs[sha] = blobid

    def getBlobs(self, path):
        """
        Return a dictionary of commit -> blob mappings for the given path.
        """
        pathid = hashlib.sha1(path).hexdigest()
        return self._paths[pathid]

    def __str__(self):
        lines = []
        for (pathid, blobs) in self._paths.iteritems():
            lines.append('path %s' % pathid)
            for (commit, blobid) in blobs.iteritems():
                lines.append("%s %s" % (blobid, commit))

        return "\n".join(lines)

def bomFromSegment(repo, segment):
    """
    Construct a BOM (bill of material) for a given segment
    """

    bom = BOM()

    # Initial tree at the head of the segment
    bom.startCommit()

    out = repo.git.ls_tree(segment[0], no_abbrev=True, r=True)
    for line in out.splitlines():
        (mode, t, sha, path) = shlex.split(line)
        bom.addBlob(path, sha)

    bom.endCommit(segment[0])

    args = [segment[0], "^%s" % segment[-1], '--']
    out = repo.git.log(*args, no_abbrev=True, raw=True, format="format:%H %ct")

    bom.startCommit()
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
        bom.endCommit(commit)

        # Add blobs to new commit
        bom.startCommit()

        for line in lines:
            if (line[0] != ':'):
                continue

            (prevmode, newmode, prevsha, newsha, op, path) = shlex.split(line[1:])
            bom.addBlob(path, prevsha)

    bom.endCommit(segment[-1])

    return bom

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
