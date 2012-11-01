from .bomwalk import BOMWalk

class TestingPlan(object):
    def __init__(self, ctl, patches, filters):
        self._ctl = ctl
        self._patches = patches
        self._filters = filters

    def construct(self, boms):
        result = {}

        for (sid, bom) in boms.iteritems():
            blobs_by_patch = {}
            walk = BOMWalk(bom)

            for (pid, p) in self._patches.iteritems():
                blobs_by_patch[pid] = {}
                walk.watch(pid, p.affected)

            for (commit, pid, paths) in walk.walk():
                if self._reject_commit(commit):
                    continue

                blobs_by_patch[pid].update(paths)

                patchkey = tuple((pid, blobid) for blobid in blobs_by_patch[pid].itervalues())
                result[patchkey] = commit

        return result

    def _reject_commit(self, commit):
        for f in self._filters:
            if not f.filter(commit):
                return True

        return False
