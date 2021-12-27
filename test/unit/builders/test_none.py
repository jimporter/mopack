import os
from unittest import mock

from . import BuilderTest, MockPackage, through_json

from mopack.builders import Builder
from mopack.builders.none import NoneBuilder
from mopack.sources.sdist import DirectoryPackage


class TestNoneBuilder(BuilderTest):
    builder_type = NoneBuilder

    def pkgconfdir(self, name, pkgconfig='pkgconfig'):
        return os.path.join(self.srcdir, pkgconfig)

    def check_build(self, builder, extra_args=[]):
        with mock.patch('subprocess.run') as mcall:
            builder.build(self.pkgdir, self.srcdir)
            mcall.assert_not_called()

    def test_basic(self):
        pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builder = self.make_builder(pkg)
        self.assertEqual(builder.name, 'foo')
        self.check_build(builder)

        with mock.patch('subprocess.run') as mcall:
            builder.deploy(pkg, self.pkgdir)
            mcall.assert_not_called()

    def test_clean(self):
        pkg = MockPackage(srcdir=self.srcdir, _options=self.make_options())
        builder = self.make_builder(pkg)

        with mock.patch('shutil.rmtree') as mrmtree:
            builder.clean(pkg, self.pkgdir)
            mrmtree.assert_not_called()

    def test_usage(self):
        opts = self.make_options()
        pkg = DirectoryPackage('foo', path=self.srcdir, build='none',
                               usage='pkg_config', _options=opts,
                               config_file=self.config_file)
        pkg.get_usage(None, self.pkgdir)

    def test_rehydrate(self):
        opts = self.make_options()
        builder = NoneBuilder(MockPackage('foo', _options=opts))
        data = through_json(builder.dehydrate())
        self.assertEqual(builder, Builder.rehydrate(data, _options=opts))

    def test_upgrade(self):
        opts = self.make_options()
        data = {'type': 'none', '_version': 0, 'name': 'foo'}
        with mock.patch.object(NoneBuilder, 'upgrade',
                               side_effect=NoneBuilder.upgrade) as m:
            pkg = Builder.rehydrate(data, _options=opts)
            self.assertIsInstance(pkg, NoneBuilder)
            m.assert_called_once()
