import os
from unittest import mock

from .. import OptionsTest, MockPackage, through_json  # noqa: F401

from mopack.config import Config
from mopack.metadata import Metadata
from mopack.options import ExprSymbols


class BuilderTest(OptionsTest):
    srcdir = os.path.abspath('/path/to/src')
    pkgdir = os.path.abspath('/path/to/builddir/mopack')
    symbols = ExprSymbols(variable='foo').augment(
        path_bases=['srcdir'], env={'BASE': 'base'}
    )

    def setUp(self):
        super().setUp()
        self.metadata = Metadata(self.pkgdir)

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def package_fetch(self, pkg):
        with mock.patch('mopack.log.pkg_fetch'), \
             mock.patch('mopack.config.load'):
            return pkg.fetch(self.metadata, Config([]))

    def make_options(self, builder_type=None, *, common_options=None,
                     this_options=None, deploy_dirs=None, config_file=None):
        options = super().make_options(common_options, deploy_dirs)
        if this_options:
            type = (builder_type or self.builder_type).type
            options.builders[type].accumulate(
                this_options, _symbols=options.expr_symbols,
                config_file=config_file or self.config_file
            )
        return options

    def make_package(self, name, builder_type=None, *, common_options=None,
                     this_options=None, deploy_dirs=None, **kwargs):
        options = self.make_options(
            builder_type, common_options=common_options,
            this_options=this_options, deploy_dirs=deploy_dirs
        )
        return MockPackage(name, srcdir=self.srcdir, _options=options,
                           **kwargs)

    def make_package_and_builder(self, name, builder_type=None, *,
                                 common_options=None, this_options=None,
                                 deploy_dirs=None, pkg_args={}, **kwargs):
        builder_type = builder_type or self.builder_type
        pkg = self.make_package(
            name, builder_type, common_options=common_options,
            this_options=this_options, deploy_dirs=deploy_dirs,
            **pkg_args
        )
        pkg.builder = builder_type(pkg, _symbols=pkg._builder_expr_symbols,
                                   **kwargs)
        return pkg
