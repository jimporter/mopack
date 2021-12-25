import os

from .. import OptionsTest, MockPackage, through_json  # noqa: F401


class BuilderTest(OptionsTest):
    srcdir = os.path.abspath('/path/to/src')
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.pkgdir, 'build', name, pkgconfig)

    def make_options(self, builder_type=None, *, common_options=None,
                     this_options=None, deploy_paths=None, config_file=None):
        options = super().make_options(common_options, deploy_paths)
        if this_options:
            type = (builder_type or self.builder_type).type
            options.builders[type].accumulate(
                this_options, _symbols=options.expr_symbols,
                config_file=config_file or self.config_file
            )
        return options

    def make_builder(self, *args, common_options=None, this_options=None,
                     deploy_paths=None, usage=None, **kwargs):
        if len(args) == 1:
            builder_type = self.builder_type
            pkg = args[0]
        else:
            builder_type, pkg = args

        if isinstance(pkg, str):
            options = self.make_options(
                builder_type, common_options=common_options,
                this_options=this_options, deploy_paths=deploy_paths
            )
            pkg = MockPackage(pkg, srcdir=self.srcdir, _options=options)

        return builder_type(pkg, **kwargs)
