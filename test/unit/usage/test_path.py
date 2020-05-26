from . import UsageTest

from mopack.usage.path import PathUsage


class TestPath(UsageTest):
    usage_type = PathUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['foo'],
        })

    def test_include_path(self):
        usage = self.make_usage('foo', include_path='include')
        self.assertEqual(usage.include_path, ['include'])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': ['/srcdir/include'],
            'library_path': [], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', include_path=['include'])
        self.assertEqual(usage.include_path, ['include'])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': ['/srcdir/include'],
            'library_path': [], 'libraries': ['foo'],
        })

    def test_library_path(self):
        usage = self.make_usage('foo', library_path='lib')
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, ['lib'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [],
            'library_path': ['/builddir/lib'], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', library_path=['lib'])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, ['lib'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [],
            'library_path': ['/builddir/lib'], 'libraries': ['foo'],
        })

    def test_libraries(self):
        usage = self.make_usage('foo', libraries='bar')
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=['bar'])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=None)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': [],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'library', 'name': 'bar'},
        ])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'guess', 'name': 'bar'},
        ])
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'bar'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
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
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': [{'type': 'framework', 'name': 'bar'}],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.get_usage(['sub'], '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['foo_sub'],
        })

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_required)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(['sub'], '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar', 'foo_sub'],
        })

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(['sub'], '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['foo', 'foo_sub'],
        })

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_optional)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(['sub'], '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['bar', 'foo_sub'],
        })

    def test_boost(self):
        submodules = {'names': '*', 'required': False}

        usage = self.make_usage('boost', submodules=submodules)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': [],
        })
        self.assertEqual(usage.get_usage(['thread'], '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['boost_thread'],
        })

        usage = self.make_usage('boost', libraries=['boost'],
                                submodules=submodules)
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['boost'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['boost'],
        })
        self.assertEqual(usage.get_usage(['thread'], '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['boost', 'boost_thread'],
        })

    def test_target_platform(self):
        usage = self.make_usage('gl', general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['GL'],
        })

        usage = self.make_usage('gl', general_options={
            'target_platform': 'darwin',
        })
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': [{'type': 'framework', 'name': 'OpenGL'}],
        })

        usage = self.make_usage('gl', libraries=['gl'], general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.include_path, [])
        self.assertEqual(usage.library_path, [])
        self.assertEqual(usage.libraries, ['gl'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
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
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': 'path', 'include_path': [], 'library_path': [],
            'libraries': ['GL'],
        })

    def test_invalid(self):
        usage = self.make_usage('foo')
        with self.assertRaises(ValueError):
            usage.get_usage(None, None, None)
