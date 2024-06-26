import os

from .. import OptionsTest, MockPackage, through_json  # noqa: F401

from mopack.metadata import Metadata


class LinkageTest(OptionsTest):
    pkgdir = os.path.abspath('/builddir/mopack')
    srcdir = os.path.abspath('/srcdir')
    builddir = os.path.abspath('/builddir')

    def setUp(self):
        super().setUp()
        self.metadata = Metadata(self.pkgdir)

    def make_linkage(self, *args, common_options=None, deploy_dirs=None,
                     submodules=None, **kwargs):
        if len(args) == 1:
            linkage_type = self.linkage_type
            pkg = args[0]
        else:
            linkage_type, pkg = args

        if isinstance(pkg, str):
            options = self.make_options(common_options, deploy_dirs)
            pkg = MockPackage(pkg, srcdir=self.srcdir, builddir=self.builddir,
                              submodules=submodules, _options=options)

        return linkage_type(pkg, _symbols=pkg._linkage_expr_symbols, **kwargs)
