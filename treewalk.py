# Tree segmentation and -walking algorithm.
#
# Segmentation: Split up a git history into sequences of commits where every
# commit has exactly one parent. The first commit in a segment therefore either
# has 0 or >1 parent.

import shlex
import pprint
from collections import namedtuple

Treenode = namedtuple('Treenode', 'mode type sha path')

def segmentize(repo, heads = None, exclude = None, before = None, after = None):
    if heads == None:
        heads = repo.git.for_each_ref("refs/heads", format="%(refname)").splitlines()

    if exclude == None:
        exclude = []

    mergeheads = [heads]
    exargs = map(lambda a: "^%s" % a, exclude)
    args = heads + exargs + ['--']

    out = repo.git.log(*args, format='format:%P', all=True, merges=True, no_abbrev=True)
    for line in out.splitlines():
        mergeheads.append(line.strip().split())

    # Flatten mergeheads into points of interest
    poi = set([item for sublist in mergeheads for item in sublist])

    # Walk through heads and determine merge-bases
    for heads in mergeheads:
        for pair in zip(heads[:-1], heads[1:]):

            base = repo.git.merge_base(*(list(pair) + exargs + ['--'])).strip()
            if base != '':
                poi.add(base)

    # Order points of interests by date
    return repo.git.rev_list(*(heads + list(poi)), no_walk=True).split()


def walk(repo, head = None, exclude = None):
    pathmap = {}
    prevcommit = None

    # Build up pathmap
    out = repo.git.ls_tree(head, no_abbrev=True, r=True)
    for line in out.splitlines():
        node = Treenode(*shlex.split(line))
        pathmap[node.path] = node

    args = [head] + map(lambda a: "^%s" % a, exclude) + ['--']
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
    pois = segmentize(r)
    for poi in pois:
        print poi 
#    print segments

##    walker = Treewalk(r)
##    walker.walk()
#    
##    pprint.pprint(segments)
#
#    print "Need to examine %d segments" % len(segments)
#    empty = 0
#    for segment in segments:
#        (head, exclude) = segment
#        walk(r, head, exclude)
##        exargs = map(lambda a: "^%s" % a, exclude)
###        repo.git.log
###        print self.repo.git.log(*args, no_abbrev=True, raw=True, format="format:%H %ct")
##        out = r.git.log(*([include] + exargs), no_abbrev=True, format="format:%H")
##        if out.strip() == '':
##            empty += 1
#
##    print "Empty segments: %d" % empty
