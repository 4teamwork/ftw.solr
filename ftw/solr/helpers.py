from functools import partial
from itertools import izip


MAXCHUNKSIZE = 1 << 16


def group_by_two(iterable):
    # group_by_two('ABCDEFG') --> AB CD EF
    args = [iter(iterable)] * 2
    return izip(*args)


def chunked_file_reader(open_file, chunk_size=MAXCHUNKSIZE):
    for chunk in iter(partial(open_file.read, chunk_size), ''):
        yield chunk


def http_chunked_encoder(iterable):
    for data in iterable:
        chunk_size = '%s\r\n' % hex(len(data))[2:]
        chunk_data = '%s\r\n' % data
        chunk = chunk_size + chunk_data
        yield chunk

    # last chunk
    yield '0\r\n\r\n'
