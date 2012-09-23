import os, re
from datetime import datetime

class PatchParser(object):
    """
    Extract hunks from patchfiles and create one new file per hunk.
    """

    # Regex for matching a hunk
    phunk = re.compile(r'^@@ -(\d+)(,(\d+))?')

    def __init__(self):
        self.reset()

    def reset(self):
        self.spool = 0;

        self.handlers = {
            'insert':       lambda l: False,
            'delete':       lambda l: False,
            'context':      lambda l: False,
            'old_file':     lambda l: False,
            'new_file':     lambda l: False,
            'hunk_header':  lambda l: False,
            'extra':        lambda l: False
        }

    def parse(self, source):
        """
        Process one input line (including line terminator).
        """

        for line in source:
            if self.spool > 0:
                if line.startswith('-'):
                    self.handlers['delete'](line)
                    self.spool = self.spool - 1
                elif line.startswith('+'):
                    self.handlers['insert'](line)
                else:
                    self.handlers['context'](line)
                    self.spool = self.spool - 1

            elif line.startswith('--- '):
                self.handlers['old_file'](line)

            elif line.startswith('+++ '):
                self.handlers['new_file'](line)

            else:
                result = self.phunk.match(line)
                if result:
                    self.handlers['hunk_header'](line)
    
                    # Start spooling lines following the hunk header
                    if result.group(3) == None:
                        self.spool = 1
                    else:
                        self.spool = int(result.group(3))
                else:
                    self.handlers['extra'](line)


class Patch(object):
    def __init__(self):
        self.git = None
        self.path = None
        self.pfxlen = 1

    @property
    def patchid(self):
        try:
            return self._patchid
        except AttributeError as e:
            f = open(self.path)
            self._patchid = self.git.patch_id(istream=f).split()
            f.close()
            return self._patchid

    @property
    def paths(self):
        try:
            return self._new_paths.union(self._old_paths)
        except AttributeError as e:
            f = open(self.path)
            self._old_paths = set()
            self._new_paths = set()

            def add_old_path(line):
                path = line[3:]

                # Strip prefix (-p parameter)
                if (self.pfxlen > 0):
                    (prefix, path) = path.split("/", self.pfxlen)

                self._old_paths.add(path.rstrip())

            def add_new_path(line):
                path = line[3:]

                # Strip prefix (-p parameter)
                if (self.pfxlen > 0):
                    (prefix, path) = path.split("/", self.pfxlen)

                self._new_paths.add(path.rstrip())

            p = PatchParser()
            p.handlers['old_file'] = add_old_path
            p.handlers['new_file'] = add_new_path
            p.parse(f)
            f.close()

            return self._new_paths.union(self._old_paths)

    @property
    def new_paths(self):
        try:
            return self._new_paths
        except AttributeError:
            self.paths
            return self._new_paths

    @property
    def old_paths(self):
        try:
            return self._old_paths
        except AttributeError:
            self.paths
            return self._old_paths

    @property
    def mtime(self):
        try:
            return self._mtime
        except AttributeError as e:
            stat = os.stat(self.path)
            self._mtime = datetime.fromtimestamp(stat.st_mtime)
            return self._mtime

class PatchFactory(object):
    def __init__(self, git):
        self.git = git

    def constructPatch(self, path, pfxlen=1):
        patch = Patch()
        patch.git = self.git
        patch.path = path 
        patch.pfxlen = pfxlen
        return patch

class RevListArgsFactory(object):
    def __init__(self, *args, **kwargs):
        self.args = list(args)
        self.kwargs = kwargs

    def constructArgsForPatch(self, patch):
        paths = list(patch.paths)
        if len(paths) == 0:
            raise Exception('No paths in patch')

        args = self.args + ['--'] + paths
        kwargs = self.kwargs.copy()
        kwargs.setdefault('after', patch.mtime)

        return (args, kwargs)

class HistoryWindow(object):
    def __init__(self):
        self.top = None
        self.bottom = None
        self.mindate = None
        self.maxdate = None

if __name__ == '__main__':
    import sys, pprint
    from git import Repo

    repo = Repo('.')

    if repo.git.status(porcelain=True) != '':
        print "Your git repository contains modified or untracked files. Cannot continue."
        sys.exit(1)

    pf = PatchFactory(repo.git)
    af = RevListArgsFactory('8.x', '^7.x')

    patches = []
    for patchpath in sys.argv[1:]:
        for pfxlen in (1, 0):
            try:
                patch = pf.constructPatch(patchpath, pfxlen)
                (args, kwargs) = af.constructArgsForPatch(patch)
                print "Adding patch %s with pfxlen %d" % (patchpath, pfxlen)
                patches.append((patch, args, kwargs))
                break
            except:
                pass

    plan = {}
    for (patchobj, args, kwargs) in patches:
        print "Examining patch %s" % (patchobj.path)
        out = repo.git.rev_list(*args, **kwargs)

        for commit in out.splitlines():
            patches = plan.setdefault(commit, list())
            patches.append(patchobj)

    for (commit, patches) in plan.iteritems():
        paths = set()

        for patch in patches:
            paths.update(patch.old_paths)

        try:
            paths.remove('/dev/null')
        except KeyError:
            pass

        args = [commit, '--']
        args.extend(paths)

        out = repo.git.ls_tree(*args, r=True)
        pathmap = dict()
        for line in out.splitlines():
            (m, t, oid, path) = line.split(None, 4)
            pathmap[path] = oid

        for patch in patches:
            if len(patch.old_paths.difference(pathmap.keys())) > 0:
                # No point on trying to apply this patch. Some paths are
                # missing.
                continue

            # FIXME: Check cache

            # Checkout commit
            repo.git.checkout(commit)
            repo.git.apply(patch.path)
            newpatch = repo.git.diff()

            # FIXME: Parse cache and record lines

            # FIXME: Update cache
            repo.git.clean(f=True, x=True, d=True, q=True)

        pprint.pprint(pathmap)

#    pprint.pprint(plan)
