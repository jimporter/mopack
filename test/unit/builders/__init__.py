import os

from .. import OptionsTest, MockPackage, through_json  # noqa: F401

from mopack.metadata import Metadata


class BuilderTest(OptionsTest):
    srcdir = os.path.abspath('/path/to/src')
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def setUp(self):
        super().setUp()
        self.metadata = Metadata(self.pkgdir)

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

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
                                 deploy_dirs=None, **kwargs):
        builder_type = builder_type or self.builder_type
        pkg = self.make_package(
            name, builder_type, common_options=common_options,
            this_options=this_options, deploy_dirs=deploy_dirs
        )
        pkg.builder = builder_type(pkg, **kwargs)
        return pkg
