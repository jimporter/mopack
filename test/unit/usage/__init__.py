import os

from .. import OptionsTest, MockPackage, through_json  # noqa: F401

from mopack.metadata import Metadata


class UsageTest(OptionsTest):
    pkgdir = os.path.abspath('/builddir/mopack')
    srcdir = os.path.abspath('/srcdir')
    builddir = os.path.abspath('/builddir')

    def setUp(self):
        super().setUp()
        self.metadata = Metadata(self.pkgdir)

    def make_usage(self, *args, common_options=None, deploy_paths=None,
                   submodules=None, **kwargs):
        if len(args) == 1:
            usage_type = self.usage_type
            pkg = args[0]
        else:
            usage_type, pkg = args

        if isinstance(pkg, str):
            options = self.make_options(common_options, deploy_paths)
            pkg = MockPackage(pkg, srcdir=self.srcdir, builddir=self.builddir,
                              submodules=submodules, _options=options)

        return usage_type(pkg, **kwargs)
