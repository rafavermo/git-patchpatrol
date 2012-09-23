import os.path
import pickle

class FilesystemResultCache(object):
    def __init__(self):
        self.directory = None
        self.pfxlen = 2

    def exists(self, blobid, patchid):
        return os.path.isfile(self._construct_path(blobid, patchid))

    def get(self, blobid, patchid):
        f = open(self._construct_path(blobid, patchid))
        content = pickle.load(f)
        f.close()

        return content

    def put(self, blobid, patchid, result):
        path = self._construct_path(blobid, patchid)
        dirname = os.path.dirname(path)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        f = open(path, 'w')
        pickle.dump(result, f)
        f.close

    def _construct_path(self, blobid, patchid):
        return os.path.join(self.directory,
            blobid[0:self.pfxlen],
            blobid[self.pfxlen:],
            patchid[0:self.pfxlen],
            patchid[self.pfxlen:])

