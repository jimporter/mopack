from .. import OptionsTest, through_json  # noqa: F401


class SourceTest(OptionsTest):
    def make_options(self, pkg_type=None, *, common_options=None,
                     this_options=None, deploy_paths=None, config_file=None):
        options = super().make_options(common_options, deploy_paths)
        if this_options:
            source = (pkg_type or self.pkg_type).source
            options.sources[source].accumulate(
                this_options, _symbols=options.expr_symbols,
                config_file=config_file or self.config_file
            )
        return options

    def make_package(self, *args, common_options=None, this_options=None,
                     deploy_paths=None, **kwargs):
        if len(args) == 1:
            pkg_type = self.pkg_type
            name = args[0]
        else:
            pkg_type, name = args

        kwargs.setdefault('config_file', self.config_file)
        opts = self.make_options(pkg_type, common_options=common_options,
                                 this_options=this_options,
                                 deploy_paths=deploy_paths)
        return pkg_type(name, _options=opts, **kwargs)
