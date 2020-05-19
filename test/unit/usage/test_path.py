from . import UsageTest

from mopack.usage.path import PathUsage


class TestPath(UsageTest):
    usage_type = PathUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['foo'],
        })

    def test_include_path(self):
        usage = self.make_usage('foo', include_path='include')
        self.assertEqual(usage.include_path, ['include'])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': ['/srcdir/include'],
            'library_path': [], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', include_path=['include'])
        self.assertEqual(usage.include_path, ['include'])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': ['/srcdir/include'],
            'library_path': [], 'libraries': ['foo'],
        })

    def test_library_path(self):
        usage = self.make_usage('foo', library_path='lib')
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, ['lib'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [],
            'library_path': ['/builddir/lib'], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', library_path=['lib'])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, ['lib'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [],
            'library_path': ['/builddir/lib'], 'libraries': ['foo'],
        })

    def test_libraries(self):
        usage = self.make_usage('foo', libraries='bar')
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=['bar'])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=None)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': [],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'library', 'name': 'bar'},
        ])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'guess', 'name': 'bar'},
        ])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'bar'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [
            {'type': 'framework', 'name': 'bar'},
        ])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': [{'type': 'framework', 'name': 'bar'}],
        })

    def test_target_platform(self):
        usage = self.make_usage('gl', general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['GL'],
        })

        usage = self.make_usage('gl', general_options={
            'target_platform': 'darwin',
        })
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': [{'type': 'framework', 'name': 'OpenGL'}],
        })

        usage = self.make_usage('gl', libraries=['gl'], general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['gl'])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['gl'],
        })

        usage = self.make_usage(
            'foo', libraries=[{'type': 'guess', 'name': 'gl'}],
            general_options={'target_platform': 'linux'}
        )
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.usage('/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['GL'],
        })

    def test_invalid(self):
        usage = self.make_usage('foo')
        with self.assertRaises(ValueError):
            usage.usage(None, None)
