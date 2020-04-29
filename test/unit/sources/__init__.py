from .. import OptionsTest


class SourceTest(OptionsTest):
    def set_options(self, pkg, global_options=None):
        options = self.make_options()
        if global_options:
            options['sources'][pkg.source].accumulate(global_options)
        pkg.set_options(options)

    def make_package(self, *args, set_options=True, global_options=None,
                     **kwargs):
        if len(args) == 1:
            pkg_type = self.pkg_type
            name = args[0]
        else:
            pkg_type, name = args

        kwargs.setdefault('config_file', self.config_file)
        pkg = pkg_type(name, **kwargs)

        if set_options:
            self.set_options(pkg, global_options)
        return pkg
