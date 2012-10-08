from collections import namedtuple

class BOMEntry(namedtuple('Changeset', 'id change remove')):
    pass


class BOMAssembler(object):
    def __init__(self):
        self._entries = []

    def startEntry(self):
        self._change = {}
        self._remove = []
        self._commitid = None

    def setCommitId(self, commitid):
        self._commitid = commitid

    def changeBlob(self, pathid, blobid):
        self._change[pathid] = blobid

    def removeBlob(self, pathid):
        self._remove.append(pathid)

    def endEntry(self):
        if self._commitid is None:
            return

        if not self._change and not self._remove:
            return

        self._entries.append(BOMEntry(self._commitid, self._change, self._remove))

    def getEntries(self):
        return self._entries


