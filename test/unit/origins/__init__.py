import os

from .. import OptionsTest, through_json  # noqa: F401

from mopack.iterutils import slice_dict
from mopack.metadata import Metadata


class OriginTest(OptionsTest):
    config_file = os.path.abspath('/path/to/mopack.yml')
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def setUp(self):
        super().setUp()
        self.metadata = Metadata(self.pkgdir)

    def make_options(self, pkg_type=None, *, this_options=None,
                     config_file=None, common_options=None, deploy_dirs=None,
                     auto_link=False):
        options = super().make_options(common_options, deploy_dirs, auto_link)
        if this_options:
            origin = (pkg_type or self.pkg_type).origin
            options.origins[origin].accumulate(
                this_options, _symbols=options.expr_symbols,
                config_file=config_file or self.config_file
            )
        return options

    def make_package(self, *args, **kwargs):
        if len(args) == 1:
            pkg_type = self.pkg_type
            name = args[0]
        else:
            pkg_type, name = args

        kwargs.setdefault('config_file', self.config_file)
        options_kwargs = slice_dict(kwargs, {
            'this_options', 'common_options', 'deploy_dirs', 'auto_link',
        })
        opts = self.make_options(pkg_type, **options_kwargs)
        return pkg_type(name, _options=opts, **kwargs)
