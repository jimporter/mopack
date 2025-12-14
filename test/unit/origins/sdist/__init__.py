import os
from unittest import mock

from .. import OriginTest, through_json  # noqa: F401
from ... import assert_logging, mock_open_log

from mopack.dependencies import Dependency
from mopack.iterutils import iterate

mock_bfgclean = 'mopack.builders.bfg9000.Bfg9000Builder.clean'


class SDistTestCase(OriginTest):
    config_file = os.path.abspath('/path/to/mopack.yml')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        if name is None:
            return os.path.join(self.pkgdir, pkgconfig)
        else:
            return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def make_package(self, *args, fetch=False, **kwargs):
        pkg = super().make_package(*args, **kwargs)
        if fetch:
            self.package_fetch(pkg)
        return pkg

    def check_linkage(self, pkg, *, submodules=None, linkage=None):
        if linkage is None:
            pcnames = ([] if pkg.submodules and pkg.submodule_required else
                       [pkg.name])
            pcnames.extend('{}_{}'.format(pkg.name, i)
                           for i in iterate(submodules))
            linkage = {'name': str(Dependency(pkg.name, submodules)),
                       'type': 'pkg_config', 'pcnames': pcnames,
                       'pkg_config_path': [self.pkgconfdir('foo')]}

        with mock.patch('mopack.linkages.path_system.file_outdated',
                        return_value=False):
            self.assertEqual(pkg.get_linkage(self.metadata, submodules),
                             linkage)

    def check_resolve(self, pkg, *, extra_args=[], env={}):
        builddir = os.path.join(self.pkgdir, 'build', pkg.name)
        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('mopack.builders.ninja.pushd'), \
             mock.patch('mopack.log.LogFile.check_call') as mcall:
            with assert_logging([('resolve', pkg.name)]):
                pkg.resolve(self.metadata)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
            mcall.assert_has_calls([
                mock.call(['bfg9000', 'configure', builddir] + extra_args,
                          env=env),
                mock.call(['ninja'], env=env),
            ])

    def make_builder(self, builder_type, pkg, **kwargs):
        return builder_type(pkg, _symbols=pkg._builder_expr_symbols, **kwargs)


def mock_open_after_first(*args, **kwargs):
    _open = open
    mock_open = mock.mock_open(*args, **kwargs)

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        return _open(*args, **kwargs)

    mock_open.side_effect = non_mock
    return mock_open
