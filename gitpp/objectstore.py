class ObjectStore(object):
    def __init__(self, ids, kvbulk, factory):
        self._ids = ids
        self._kvbulk = kvbulk
        self._factory = factory

        self._objects = {}
        self._newobjects = {}


    def load(self, use_kvbulk=True, use_factory=True):
        if self._kvbulk and use_kvbulk:
            existence = self._kvbulk.exist(self._ids)

            # Try to load existing object for each id
            self._objects = self._kvbulk.load([oid for (oid, exists) in existence.iteritems() if exists])
        else:
            existence = dict((oid, False) for oid in self._ids)


        if self._factory and use_factory:
            # Construct object for each id missing in the kvstore
            self._newobjects = self._factory.create([oid for (oid, exists) in existence.iteritems() if not exists])


    def dump(self):
        if self._kvbulk:
            self._kvbulk.dump(self._newobjects.keys(), self._newobjects)


    def get_all(self):
        result = dict(self._objects)
        result.update(self._newobjects)
        return result


    def get_existing(self):
        return self._objects


    def get_new(self):
        return self._newobjects
