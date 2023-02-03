import os
from unittest import mock

from .. import OriginTest, through_json  # noqa: F401
from ... import assert_logging, mock_open_log

from mopack.iterutils import iterate
from mopack.types import dependency_string

mock_bfgclean = 'mopack.builders.bfg9000.Bfg9000Builder.clean'


class SDistTestCase(OriginTest):
    config_file = os.path.abspath('/path/to/mopack.yml')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        if name is None:
            return os.path.join(self.pkgdir, pkgconfig)
        else:
            return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def check_resolve(self, pkg, *, submodules=None, usage=None):
        if usage is None:
            pcnames = ([] if pkg.submodules and pkg.submodules['required'] else
                       ['foo'])
            pcnames.extend('foo_{}'.format(i) for i in iterate(submodules))
            usage = {'name': dependency_string(pkg.name, submodules),
                     'type': 'pkg_config', 'pcnames': pcnames,
                     'pkg_config_path': [self.pkgconfdir('foo')]}

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run'):
            with assert_logging([('resolve', pkg.name)]):
                pkg.resolve(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')

        with mock.patch('mopack.usage.path_system.file_outdated',
                        return_value=False):
            self.assertEqual(pkg.get_usage(self.metadata, submodules), usage)

    def make_builder(self, builder_type, pkg, **kwargs):
        return builder_type(pkg, **kwargs)


def mock_open_after_first(*args, **kwargs):
    _open = open
    mock_open = mock.mock_open(*args, **kwargs)

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        return _open(*args, **kwargs)

    mock_open.side_effect = non_mock
    return mock_open
