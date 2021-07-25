import json
import os
import pkg_resources
from contextlib import contextmanager
from io import StringIO
from unittest import mock, TestCase

from mopack.options import Options

# Make sure the entry points are loaded so unit tests can reference them as
# needed.
pkg_resources.get_entry_map('mopack')


@contextmanager
def mock_open_log(new=None, *args, **kwargs):
    with mock.patch('builtins.open', new or mock.mock_open(),
                    *args, **kwargs) as m, \
         mock.patch('os.makedirs'):
        yield m


def mock_open_data(read_data):
    return lambda *args, **kwargs: StringIO(read_data)


def mock_open_files(files):
    def wrapper(filename, *args, **kwargs):
        return StringIO(files[os.path.basename(filename)])

    return wrapper


class MockPackage:
    def __init__(self, name='foo'):
        self.name = name


def through_json(data):
    return json.loads(json.dumps(data))


class OptionsTest(TestCase):
    config_file = os.path.abspath('/path/to/options.yml')

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

    def make_options(self, common_options=None, deploy_paths=None):
        options = Options(deploy_paths)
        if common_options:
            options.common.accumulate(common_options)
        with mock.patch.object(os, 'environ', return_value={}):
            options.common.finalize()

        for i in pkg_resources.iter_entry_points('mopack.sources'):
            opts_type = i.load().Options
            if opts_type:
                options.sources[opts_type.source] = opts_type()

        for i in pkg_resources.iter_entry_points('mopack.builders'):
            opts_type = i.load().Options
            if opts_type:
                options.builders[opts_type.type] = opts_type()

        return options
