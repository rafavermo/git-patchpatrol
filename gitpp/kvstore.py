import collections
from abc import ABCMeta, abstractmethod

class KVStore:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __getitem__(self, key):
        pass

    @abstractmethod
    def __setitem__(self, key, value):
        pass

    @abstractmethod
    def __delitem__(self, key):
        pass

    @abstractmethod
    def __contains__(self, key):
        pass

KVStore.register(collections.MutableMapping)
