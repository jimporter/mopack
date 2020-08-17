import os
import pkg_resources
from contextlib import contextmanager
from unittest import mock, TestCase

from mopack.config import CommonOptions

# Make sure the entry points are loaded so unit tests can reference them as
# needed.
pkg_resources.get_entry_map('mopack')


@contextmanager
def mock_open_log(new=None, *args, **kwargs):
    with mock.patch('builtins.open', new or mock.mock_open(),
                    *args, **kwargs) as m, \
         mock.patch('os.makedirs'):
        yield m


class OptionsTest(TestCase):
    def make_options(self, common_options=None):
        options = {'common': CommonOptions(), 'sources': {}, 'builders': {}}
        if common_options:
            options['common'].accumulate(common_options)
        with mock.patch.object(os, 'environ', return_value={}):
            options['common'].finalize()

        for i in pkg_resources.iter_entry_points('mopack.sources'):
            opts_type = i.load().Options
            if opts_type:
                options['sources'][opts_type.source] = opts_type()

        for i in pkg_resources.iter_entry_points('mopack.builders'):
            opts_type = i.load().Options
            if opts_type:
                options['builders'][opts_type.type] = opts_type()

        return options
