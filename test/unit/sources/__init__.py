from .. import OptionsTest


class SourceTest(OptionsTest):
    def set_options(self, pkg, common_options=None, this_options=None):
        options = self.make_options(common_options)
        if this_options:
            options['sources'][pkg.source].accumulate(this_options)
        pkg.set_options(options)

    def make_package(self, *args, set_options=True, common_options=None,
                     this_options=None, symbols=None, **kwargs):
        if symbols is None:
            symbols = self.symbols

        if len(args) == 1:
            pkg_type = self.pkg_type
            name = args[0]
        else:
            pkg_type, name = args

        kwargs.setdefault('config_file', self.config_file)
        pkg = pkg_type(name, symbols=symbols, **kwargs)

        if set_options:
            self.set_options(pkg, common_options, this_options)
        return pkg
