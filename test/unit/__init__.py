import importlib_metadata as metadata
import json
import logging
import os
import re
from contextlib import contextmanager
from io import StringIO
from unittest import mock, TestCase

from mopack.options import Options


@contextmanager
def mock_open_log(new=None, *args, **kwargs):
    with mock.patch('builtins.open', new or mock.mock_open(),
                    *args, **kwargs) as m, \
         mock.patch('os.makedirs'):
        yield m


@contextmanager
def assert_logging(expected):
    def strip_ansi(s):
        return re.sub('\033\\[.*?m', '', s)

    def format_logs(logs):
        if not logs:
            return '  <none>'
        return '  ' + '\n  '.join('{}: {}'.format(*i) for i in logs)

    with mock.patch.object(logging.Logger, 'isEnabledFor',
                           return_value=True), \
         mock.patch.object(logging.Logger, 'handle') as m:
        yield
        # `i[-2]` gets the positional arguments. This is just for compatibility
        # with Python 3.7 and older. (In 3.8+, we'd use `i.args`).
        logs = [(i[-2][0].levelname, strip_ansi(i[-2][0].getMessage()))
                for i in m.mock_calls]
        if logs != expected:
            raise AssertionError('Expected logs:\n{}\nReceived:\n{}'.format(
                format_logs(expected), format_logs(logs)
            ))


class Stream(StringIO):
    def close(self):
        pass


def mock_open_data(read_data):
    return lambda *args, **kwargs: StringIO(read_data)


def mock_open_files(files):
    def wrapper(filename, *args, **kwargs):
        return StringIO(files[os.path.basename(filename)])

    return wrapper


class MockBuilder:
    def __init__(self, builddir):
        self._builddir = builddir

    def path_bases(self):
        return ('builddir',)

    def path_values(self, metadata):
        return {'builddir': self._builddir}


class MockPackage:
    def __init__(self, name='foo', *, version=None, srcdir=None, builddir=None,
                 submodules=None, _options=None):
        self.name = name
        self.submodules = submodules
        self.builder = MockBuilder(builddir) if builddir else None
        self._version = version
        self._srcdir = srcdir
        self._options = _options

    @property
    def _builder_expr_symbols(self):
        if self._srcdir:
            return self._options.expr_symbols.augment_path_bases('srcdir')
        raise AttributeError()

    @property
    def _linkage_expr_symbols(self):
        if self._srcdir:
            symbols = self._builder_expr_symbols
        else:
            symbols = self._options.expr_symbols

        if self.builder:
            symbols = symbols.augment_path_bases(*self.builder.path_bases())
        return symbols

    def path_values(self, metadata):
        return {
            **({'srcdir': self._srcdir} if self._srcdir else {}),
            **(self.builder.path_values(metadata) if self.builder else {}),
        }

    def guessed_version(self, metadata):
        return self._version


def through_json(data, *args, **kwargs):
    return json.loads(json.dumps(data, *args, **kwargs))


class OptionsTest(TestCase):
    config_file = os.path.abspath('/path/to/options.yml')

    @property
    def config_dir(self):
        return os.path.dirname(self.config_file)

    def make_options(self, common_options=None, deploy_dirs=None):
        options = Options(deploy_dirs)
        if common_options:
            options.common.accumulate(common_options)
        with mock.patch.object(os, 'environ', return_value={}):
            options.common.finalize()

        for i in metadata.entry_points(group='mopack.origins'):
            opts_type = i.load().Options
            if opts_type:
                options.origins[opts_type.origin] = opts_type()

        for i in metadata.entry_points(group='mopack.builders'):
            opts_type = i.load().Options
            if opts_type:
                options.builders[opts_type.type] = opts_type()

        return options
