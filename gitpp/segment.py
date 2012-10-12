class SegmentAssembler(object):
    def __init__(self):
        self._tails = {}
        self._segments = []
        self._commitid = None

    def startCommit(self):
        self._commitid = None
        self._parents = []
        self._children = []

    def setCommitId(self, commitid):
        self._commitid = commitid

    def setParents(self, parents):
        self._parents = parents

    def setChildren(self, children):
        self._children = children

    def endCommit(self):
        # Do nothing if no commit was started
        if self._commitid == None:
            return

        if len(self._children) == 1:
            # This commit has exactly one child. Therefore we simply can append
            # it to the appropriate segment.
            try:
                segment = self._tails.pop(self._children[0])
            except KeyError:
                segment = []
                self._segments.append(segment)
            segment.append(self._commitid)
        else:
            # Start new branch
            segment = [self._commitid]
            self._segments.append(segment)

        # Update tails
        self._tails[self._commitid] = segment

        if len(self._parents) != 1:
            # We are either a merge or an initial commit. In both cases we can
            # Close up this segment.
            self._tails.pop(self._commitid)

    def getSegments(self):
        return self._segments


def filter_segments(segments, filters):
    result = []
    for segment in segments:
        if (filter_segment(segment, filters)):
            result.append(segment)
            continue

    return result


def filter_segment(segment, filters):
    """
    Return True if any of the commits in segments is accepted by any of the
    given filters. Otherwise return False.
    """
    for commit in segment:
        for f in filters:
            if (f.filter(commit)):
                return True

    return False
