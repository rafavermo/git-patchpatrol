import collections
import os

from datetime import datetime

from gitpp import patch

class PatchfileError(Exception):
    def __init__(self, underlying, *args, **kwargs):
        super(PatchfileError, self).__init__(*args, **kwargs)
        self.underlying = underlying


class Patchfile(collections.namedtuple('Patchfile', 'path patchid mtime affected')):
    pass


class GitPatchfileFactory(object):
    def __init__(self, repo):
        self._repo = repo


    def patchid(self, path):
        istream = open(path, 'r')
        out = self._repo.git.patch_id(istream=istream)
        istream.close()

        return out.split()[0]


    def fromfile(self, path):
        try:
            pid = self.patchid(path)
        except Exception as e:
            raise PatchfileError(e, 'Unable to generate patchid from %s' % path)

        try:
            mtime = datetime.fromtimestamp(os.stat(path).st_mtime)
        except Exception as e:
            raise PatchfileError(e, 'Unable to determine mtime from %s' % path)

        affected = set()
        try:
            for (sym, data) in patch.parse(open(path, 'r')):
                if (sym == 'a'):
                    affected.add(patch.pathstrip(data))
        except patch.ParseError as e:
            raise PatchfileError(e, 'Unable to parse patch from %s' % path)

        return Patchfile(path, pid, mtime, affected)
