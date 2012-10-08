import hashlib

class BOMWalk(object):
    def __init__(self, segment, bom):
        self._segment = segment
        self._bom = bom

        # Map: key => [list of paths]
        self._paths_by_key = {}

        # Map: key => integer
        # Number of paths in the missing-path list for a given observer.
        self._paths_missing_count = {}

        # Map: path => [list of watch-keys]
        # Paths, which must become available before the listed keys will be
        # triggered for a commit.
        self._paths_missing = {}

        # Map: path => [list of watch-keys]
        # Paths, which may not go away without affecting the listed keys.
        self._paths_watched = {}


    def watch(self, key, paths):
        self._paths_missing_count[key] = 0

        for path in paths:
            keys = self._paths_missing.setdefault(path, set())
            keys.add(key)
            self._paths_missing_count[key] += 1

        self._paths_by_key[key] = paths


    def walk(self):
        # Initial commit contains all files
        for entry in self._bom:
            self._removepaths(entry.remove)
            changed = entry.change.keys()
            self._addpaths(changed)

            # Construct a set of keys which are ready.
            ready = set()
            for path in changed:
                if path not in self._paths_watched:
                    continue

                for key in self._paths_watched[path]:
                    if self._paths_missing_count[key] == 0:
                        ready.add(key)

            for key in ready:
                paths = dict((path, entry.change[path]) for path in self._paths_by_key[key] if path in entry.change)
                yield (entry.id, key, paths)


    def _addpaths(self, paths):
        for path in paths:
            if path in self._paths_watched:
                continue

            if path not in self._paths_missing:
                continue

            keys = self._paths_missing.pop(path)
            for key in keys:
                self._paths_missing_count[key] -= 1

            self._paths_watched[path] = keys


    def _removepaths(self, paths):
        for path in paths:
            if path not in self._paths_watched:
                continue

            keys = self._paths_watched.pop(path)
            for key in keys:
                self._paths_missing_count[key] += 1

            self._paths_missing[path] = keys


if __name__ == '__main__':
    import pprint
    from segmentize import segmentize
    from bom import BOM
    from cache import FilesystemResultCache
    from git import Repo


    r = Repo('.')
    segments = segmentize(r)

    cache = FilesystemResultCache()
    cache.directory='/tmp/bom-cache'

    seen = set()

    for segment in segments:
        if cache.exists(segment[0], segment[-1]):
            bom = cache.get(segment[0], segment[-1])
        else:
            bom = bomFromSegment(r, segment)

        walk = BOMWalk(segment, bom)
        walk.watch('cl', ['README.txt'])
        for (commit, key, paths) in walk.walk():
            if (key, tuple(paths.items())) in seen:
                #print '- commit: %s has identical contents as a previous one' % commit
                continue

            print commit
            #pprint.pprint(paths)
            seen.add((key, tuple(paths.items())))

