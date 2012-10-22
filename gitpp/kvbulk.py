
class KVBulkNaive(object):
    def __init__(self, kvstore):
        self._kvstore = kvstore


    def exist(self, keys):
        return dict((key, key in self._kvstore) for key in keys)


    def load(self, keys):
        return dict((key, self._kvstore[key]) for key in keys)


    def dump(self, keys, values):
        for key in keys:
            self._kvstore[key] = values[key]
