import os.path


def get_data(filename):
    """Return content from a file in the test data folder """
    filename = os.path.join(os.path.dirname(__file__), 'data', filename)
    return open(filename, 'r').read()


class MockHTTPResponse(object):
    def __init__(self, status=200, body=''):
        self.status = status
        self.body = body

    def read(self):
        return self.body


class MockBlob(object):
    def committed(self):
        return '/folder/file'
