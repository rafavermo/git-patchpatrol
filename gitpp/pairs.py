import itertools

class PairError(Exception):
    def __init__(self, tail, *args, **kwargs):
        super(PairError, self).__init__(*args, **kwargs)
        self.tail = tail


def lists_of_pairs(seq):
    """
    Divide a sequence into sublists comprising only of pairs
    (pair -> (item, -item)). Items need to implement __neg__ in order to be
    processable by this function.
    """
    stack = []
    sub = []

    for item in seq:
        sub.append(item)

        try:
            stack.remove(-item)
        except ValueError:
            stack.append(item)

        if not stack:
            yield sub
            sub = []

    if sub:
        raise PairError(sub, "Sequence has trailing objects not forming pairs.")


def overlapping_pairs(seq):
    """
    Given a sequence of items, yield sublists containing items which are *not*
    adjacent pairs. Where pair => (item, -item). Objects need to implement
    __neg__ in order to be processable by this function.
    """

    for sub in lists_of_pairs(seq):
        if len(sub) != 2:
            yield sub


def lists_of_combinations(mapseq, r):
    """
    For a list of key -> value mappings in mapseq [(k_x, v_y), ...] collect
    all keys and build r-length combinations. For each combination yield a
    sublist of key -> value mappings containing only those entries where key
    is in the combination.

    @see itertools.combinations
    """

    # Collect all keys
    keys = set(key for (key, val) in mapseq)

    # For each group configuration yield a filtered list of the input
    for comb in itertools.combinations(keys, r):
        yield [(key, val) for (key, val) in mapseq if key in comb]
