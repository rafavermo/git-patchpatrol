#from .. import logger

class GitRevListFilter(object):
    def __init__(self, repo, *args, **kwds):
        self._repo = repo
        self._commits = set()
        self._args = args
        self._kwds = kwds

        if not args and not kwds:
            self._kwds = {'all':True}


    def prepare(self):
        self._commits = self._repo.git.rev_list(*self._args, **self._kwds).splitlines()


    def cleanup(self):
        pass


    def filter(self, commit):
        return commit in self._commits
