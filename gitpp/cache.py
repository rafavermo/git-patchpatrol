import os.path
import pickle
import collections
from .kvstore import KVStore

class SimpleFSStore(KVStore):
    def __init__(self):
        self.directory = None
        self.pfxlen = 2
        self.multilevel = False

    def __getitem__(self, key):
        try:
            f = open(self._construct_path(key))
        except OSError:
            raise KeyError

        content = pickle.load(f)
        f.close()

        return content

    def __setitem__(self, key, value):
        path = self._construct_path(key)
        dirname = os.path.dirname(path)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        f = open(path, 'w')
        pickle.dump(value, f)
        f.close

    def __delitem__(self, key):
        path = self._construct_path(key)

        try:
            os.path.unlink(path)
        except OSError:
            raise KeyError

    def __contains__(self, key):
        return os.path.isfile(self._construct_path(key))

    def _construct_path(self, key):
        if not self.multilevel:
            key = (key,)

        if self.pfxlen > 0:
            path = os.path.join(self.directory,
                key[0][0:self.pfxlen],
                key[0][self.pfxlen:])
        else:
            path = os.path.join(self.directory, key[0])

        for part in key[1:]:
            path = os.path.join(path, part)

        return path


class CompositeKVStore(KVStore):
    def __init__(self, kvstore, construct = None):
        assert isinstance(kvstore, KVStore)
        self._kvstore = kvstore

        assert construct == None or callable(construct)
        self._construct = construct


    def __getitem__(self, keys):
        assert isinstance(keys, collections.Iterable)

        result = {}

        try:
            result = dict((key, self._kvstore[key]) for key in keys)
        except KeyError as e:
            if callable(self._construct):
                self._construct(keys, self._kvstore)
            else:
                raise e

        return result


    def __setitem__(self, keys, values):
        assert isinstance(keys, collections.Iterable)

        for key in keys:
            self._kvstore[key] = values[key]


    def __delitem__(self, keys):
        assert isinstance(keys, collections.Iterable)

        for key in keys:
            del self._kvstore[key]


    def __contains__(self, keys):
        assert isinstance(keys, collections.Iterable)

        for key in keys:
            if key not in self._kvstore:
                return False

        return True
