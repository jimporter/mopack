import os
from unittest import mock

from . import BuilderTest, MockPackage, through_json
from .. import rehydrate_kwargs

from mopack.builders import Builder
from mopack.builders.none import NoneBuilder
from mopack.origins.sdist import DirectoryPackage


class TestNoneBuilder(BuilderTest):
    builder_type = NoneBuilder

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.srcdir, pkgconfig)

    def check_build(self, pkg, extra_args=[]):
        with mock.patch('subprocess.run') as mcall:
            pkg.builder.build(self.metadata, pkg)
            mcall.assert_not_called()

    def test_basic(self):
        pkg = self.make_package_and_builder('foo')
        self.assertEqual(pkg.builder.name, 'foo')
        self.check_build(pkg)

        with mock.patch('subprocess.run') as mcall:
            pkg.builder.deploy(self.metadata, pkg)
            mcall.assert_not_called()

    def test_clean(self):
        pkg = self.make_package_and_builder('foo')

        with mock.patch('shutil.rmtree') as mrmtree:
            pkg.builder.clean(self.metadata, pkg)
            mrmtree.assert_not_called()

    def test_linkage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build='none',
                               linkage='pkg_config', _options=opts,
                               config_file=self.config_file)
        self.package_fetch(pkg)
        pkg.get_linkage(self.metadata, None)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = NoneBuilder(MockPackage('foo', _options=opts),
                              _symbols=self.symbols)
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(
            data, name='foo', _options=opts, _symbols=opts.expr_symbols,
            **rehydrate_kwargs
        ))

    def test_upgrade_from_v1(self):
        opts = self.make_options()
        data = {'type': 'none', '_version': 1, 'name': 'bar'}
        with mock.patch.object(NoneBuilder, 'upgrade',
                               side_effect=NoneBuilder.upgrade) as m:
            builder = Builder.rehydrate(
                data, name='foo', _options=opts, _symbols=opts.expr_symbols,
                **rehydrate_kwargs
            )
            self.assertIsInstance(builder, NoneBuilder)
            m.assert_called_once()
