# Tree segmentation and -walking algorithm.
#
# Segmentation: Split up a git history into sequences of commits where every
# commit has exactly one parent. The first commit in a segment therefore either
# has 0 or >1 parent.

import shlex
import pprint
from collections import namedtuple
from segmentize import segmentize

Treenode = namedtuple('Treenode', 'mode type sha path')

def walk(repo, segment):
    pathmap = {}
    prevcommit = None

    # Build up pathmap
    out = repo.git.ls_tree(segment[0], no_abbrev=True, r=True)
    for line in out.splitlines():
        node = Treenode(*shlex.split(line))
        pathmap[node.path] = node

    args = [segment[0], "^%s" % segment[-1], '--']
    out = repo.git.log(*args, no_abbrev=True, raw=True, format="format:%H %ct")

    for message in out.split("\n\n"):
        if (message.strip() == ''):
            continue

        lines = message.splitlines()
        (commit, timestamp) = lines.pop(0).split()

        print commit

        # Workaround: Merge-only commits (not affecting any files) sometimes
        # are separated to following commits only with one newline, instead of
        # two. In this case we just stick with the following commit id.
        while(len(lines) > 0 and lines[0][0] != ':'):
            (commit, timestamp) = lines.pop(0).split()

        # Parse lines and fire alteration events
        prevpathmap = pathmap.copy()

        for line in lines:
            if (line[0] != ':'):
                continue

            (oldmode, newmode, oldsha, newsha, op, path) = shlex.split(line[1:])
            oldnode = Treenode(oldmode, 'blob', oldsha, path)
            newnode = Treenode(newmode, 'blob', newsha, path)

            if (op == 'M'):
                assert(pathmap[path] == newnode)
                prevpathmap[path] = oldnode

            elif (op == 'A'):
                assert(pathmap[path] == newnode)
                prevpathmap.pop(path)

            elif (op == 'D'):
                prevpathmap[path] = oldnode

        pathmap = prevpathmap

if __name__ == '__main__':
    from git import Repo

    r = Repo('.')
    segments = segmentize(r)

    print "Need to examine %d segments" % len(segments)
    for segment in segments:
        walk(r, segment)
