from contextlib import contextmanager
from unittest import mock


@contextmanager
def mock_open_log(new=None, *args, **kwargs):
    with mock.patch('builtins.open', new or mock.mock_open(),
                    *args, **kwargs) as m, \
         mock.patch('os.makedirs'):
        yield m
