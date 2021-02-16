import os
from unittest import mock

from mopack.iterutils import iterate

from .. import SourceTest, through_json  # noqa: F401
from ... import mock_open_log

mock_bfgclean = 'mopack.builders.bfg9000.Bfg9000Builder.clean'


class SDistTestCase(SourceTest):
    config_file = os.path.abspath('/path/to/mopack.yml')
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def check_resolve(self, pkg, *, submodules=None, usage=None):
        if usage is None:
            pcfiles = ([] if pkg.submodules and pkg.submodules['required'] else
                       ['foo'])
            pcfiles.extend('foo_{}'.format(i) for i in iterate(submodules))
            usage = {'type': 'pkg_config', 'path': self.pkgconfdir('foo'),
                     'pcfiles': pcfiles, 'extra_args': []}

        with mock_open_log() as mopen, \
             mock.patch('mopack.builders.bfg9000.pushd'), \
             mock.patch('subprocess.run'):  # noqa
            pkg.resolve(self.pkgdir)
            mopen.assert_called_with(os.path.join(
                self.pkgdir, 'logs', 'foo.log'
            ), 'a')
        self.assertEqual(pkg.get_usage(self.pkgdir, submodules), usage)

    def make_builder(self, builder_type, name, *, submodules=None,
                     options=None, usage=None, **kwargs):
        if options is None:
            options = self.make_options()

        builder = builder_type(name, submodules=submodules, _options=options,
                               **kwargs)
        builder.set_usage(usage, submodules=submodules)
        return builder


def mock_open_after_first(*args, **kwargs):
    _open = open
    mock_open = mock.mock_open(*args, **kwargs)

    def non_mock(*args, **kwargs):
        mock_open.side_effect = None
        return _open(*args, **kwargs)

    mock_open.side_effect = non_mock
    return mock_open
