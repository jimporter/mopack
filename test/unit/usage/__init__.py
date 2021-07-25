import os

from .. import OptionsTest, MockPackage, through_json  # noqa: F401


class UsageTest(OptionsTest):
    pkgdir = os.path.abspath('/path/to/builddir/mopack')

    def make_usage(self, *args, common_options=None, deploy_paths=None,
                   submodules=None, _path_bases=('srcdir', 'builddir'),
                   **kwargs):
        if len(args) == 1:
            usage_type = self.usage_type
            name = args[0]
        else:
            usage_type, name = args

        opts = self.make_options(common_options, deploy_paths)
        return usage_type(name, submodules=submodules, _options=opts,
                          _path_bases=_path_bases, **kwargs)
