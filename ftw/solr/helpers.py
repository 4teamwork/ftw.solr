from itertools import izip


def group_by_two(iterable):
    # group_by_two('ABCDEFG') --> AB CD EF
    args = [iter(iterable)] * 2
    return izip(*args)
