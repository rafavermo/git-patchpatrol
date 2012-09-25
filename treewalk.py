import shlex
import pprint
from collections import namedtuple

Treenode = namedtuple('Treenode', 'mode type sha path')

def segmentize(repo, include = None, exclude = None):
    if include == None:
        heads = repo.git.for_each_ref("refs/heads", format="%(refname)").splitlines()
    else:
        heads = include[:]

    if exclude == None:
        exclude = []
    else:
        exclude = exclude[:]

    result = []
    while len(heads) > 0:
        head = heads.pop(0)

        exargs = map(lambda a: "^%s" % a, exclude + heads)
        args = [head] + exargs + ['--']
        flags = {
            'format': 'format:%P',
            'merges': True,
            'no_abbrev': True
        }
    
        out = repo.git.log(*args, **flags).strip()
    
        parents = out.split()
    
        result.append((head, exclude + heads + parents))
    
        while len(parents) > 0:
            parent = parents.pop(0)
            result.append((parent, exclude + heads + parents))

    return result


class Treewalk(object):
    def __init__(self, repo, head = 'HEAD', exclude = None):
        self.repo = repo
        self.head = head

        if exclude:
            self.exclude = exclude
        else:
            self.exclude = []

        self.pathmap = None
        self.prevpathmap = None
        self.prevcommit = None

        self.listeners = {}

    def walk(self, build_content=True, indent=''):
        if build_content:
            self._build_content()

        args = [self.head]
        args.extend(self.exclude)

        out = self.repo.git.log(*args, no_abbrev=True, raw=True, format="format:%H %ct")
        for message in out.split("\n\n"):
            lines = message.splitlines()
            (commit, timestamp) = lines.pop(0).split()

            # Workaround: Merge-only commits sometimes are separated to
            # following commits only with one newline, instead of two. In this
            # case we just stick with the following commit id.
            while(len(lines) > 0 and lines[0][0] != ':'):
                (commit, timestamp) = lines.pop(0).split()

            self.handlecommit(prevcommit, commit, prevpathmap, pathmap)

            # Parse lines and fire alteration events
            self.prevpathmap = self.pathmap.copy()

            for line in lines:
                if (line[0] != ':'):
                    continue

                (oldmode, newmode, oldsha, newsha, op, path) = shlex.split(line[1:])
                oldnode = Treenode(oldmode, 'blob', oldsha, path)
                newnode = Treenode(newmode, 'blob', newsha, path)

                if (op == 'M'):
                    assert(self.pathmap[path] == newnode)
                    self.prevpathmap[path] = oldnode

                elif (op == 'A'):
                    assert(self.pathmap[path] == newnode)
                    self.prevpathmap.pop(path)

                elif (op == 'D'):
                    self.prevpathmap[path] = oldnode

            self.pathmap = self.prevpathmap

    def _build_content(self):
        self.pathmap = {}

        out = self.repo.git.ls_tree(self.head, no_abbrev=True, r=True)

        for line in out.splitlines():
            node = Treenode(*shlex.split(line))
            self.pathmap[node.path] = node

if __name__ == '__main__':
    from git import Repo
    
    r = Repo('.')
    segments = segmentize(r)

#    walker = Treewalk(r)
#    walker.walk()
    
#    pprint.pprint(segments)

    print "Need to examine %d segments" % len(segments)
    empty = 0
    for segment in segments:
        (include, exclude) = segment
        exargs = map(lambda a: "^%s" % a, exclude)
#        repo.git.log
#        print self.repo.git.log(*args, no_abbrev=True, raw=True, format="format:%H %ct")
        out = r.git.log(*([include] + exargs), no_abbrev=True, format="format:%H")
        if out.strip() == '':
            empty += 1

    print "Empty segments: %d" % empty
