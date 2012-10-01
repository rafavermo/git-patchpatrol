class SegmentAssembler(object):
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
    assembler = SegmentAssembler()

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

if __name__ == '__main__':
    import pprint
    from git import Repo
    
    r = Repo('.')
    segments = segmentize(r)
    for segment in segments:
        tip = segment[0]
        tail = segment[-1]
        print("checking %s..%s" % (tail, tip))
        commits = r.git.rev_list("%s..%s" % (tail, tip)).splitlines()
        commits.append(tail)
        if (commits != segment):
            print('commits')
            pprint.pprint(commits)
            print('segment')
            pprint.pprint(segment)
            raise Exception('fail')
