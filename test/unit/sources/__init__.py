import unittest


class SourceTest(unittest.TestCase):
    def make_package(self, *args, global_options={}, **kwargs):
        if len(args) == 1:
            pkg_type = self.pkg_type
            name = args[0]
        else:
            pkg_type, name = args

        kwargs.setdefault('config_file', self.config_file)
        pkg = pkg_type(name, **kwargs)

        if pkg_type.Options:
            opts = pkg_type.Options()
            opts.accumulate(global_options)
            pkg.set_options({opts.source: opts})
        else:
            pkg.set_options({})

        return pkg
