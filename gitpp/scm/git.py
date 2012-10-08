import shlex

_HASHREMOVE = "".zfill(40)

class _SegmentAssembler(object):
    def __init__(self):
        self._current = {}
        self._tails = {}
        self._segments = []

    def startCommit(self, sha):
        self._current['commit'] = sha 

    def setParents(self, parents):
        self._current['parents'] = parents

    def setChildren(self, children):
        self._current['children'] = children

    def endCommit(self):
        # Do nothing if no commit was started
        try:
            sha = self._current.pop('commit')
        except KeyError:
            return

        children = self._current.pop('children', [])
        if len(children) == 1:
            # This commit has exactly one child. Therefore we simply can append
            # it to the appropriate segment.
            try:
                segment = self._tails.pop(children[0])
            except KeyError:
                segment = []
                self._segments.append(segment)
            segment.append(sha)
        else:
            # Start new branch
            segment = [sha]
            self._segments.append(segment)

        # Update tails
        self._tails[sha] = segment

        parents = self._current.pop('parents', [])
        if len(parents) != 1:
            # We are either a merge or an initial commit. In both cases we can
            # Close up this segment.
            self._tails.pop(sha)

    def segments(self):
        return self._segments


def segmentize(repo, heads = None, exclude = None, before = None, after = None):
    assembler = _SegmentAssembler()

    if heads == None:
        heads = repo.git.for_each_ref("refs/heads", format="%(refname)").splitlines()

    if exclude == None:
        exclude = []

    exargs = map(lambda a: "^%s" % a, exclude)
    args = heads + exargs + ['--']

    out = repo.git.rev_list(*args, format='format:%P', children=True, full_history=True, no_abbrev=True)

    for line in out.splitlines():
        if line.startswith('commit '):
            assembler.endCommit()

            hashes = line.split()
            hashes.pop(0)
            assembler.startCommit(hashes.pop(0))
            assembler.setChildren(hashes)
        else:
            hashes = line.split()
            assembler.setParents(hashes)
    
    assembler.endCommit()
    return assembler.segments()


class BOMAssembler(object):
    def __init__(self):
        self._current = {}
        self._commits = []

    def startCommit(self):
        self._current = {}
        self._current['change'] = {}
        self._current['remove'] = []

    def changeBlob(self, pathid, blobid):
        self._current['change'][pathid] = blobid

    def removeBlob(self, pathid):
        self._current['remove'].append(pathid)

    def endCommit(self, sha):
        if len(self._current['change']) < 1:
            return

        self._current['commit'] = sha
        self._commits.append(self._current)

    def commits(self):
        return self._commits

    def __str__(self):
        lines = []
        for commit in self._commits:
            lines.append('commit %s' % commit['commit'])
            for (pathid, blobid) in commit['change'].iteritems():
                lines.append("+ %s %s" % (blobid, pathid))
            for pathid in commit['remove']:
                lines.append("- %s" % pathid)

        return "\n".join(lines)


def bom_from_segment(repo, segment):
    """
    Construct a BOMAssembler (bill of material) for a given segment
    """

    bom = BOMAssembler()

    # Initial tree at the head of the segment
    bom.startCommit()

    out = repo.git.ls_tree(segment[0], no_abbrev=True, r=True)
    for line in out.splitlines():
        (mode, t, sha, path) = shlex.split(line)
        bom.changeBlob(path, sha)

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
            if prevsha == _HASHREMOVE:
                bom.removeBlob(path)
            else:
                bom.changeBlob(path, prevsha)

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
        print bom
        cache.put(segment[0], segment[-1], bom)
