from . import UsageTest

from mopack.types import FieldError
from mopack.usage.path_system import PathUsage, SystemUsage


class TestPath(UsageTest):
    usage_type = PathUsage
    type = 'path'

    def check_usage(self, usage, *, include_path=[], library_path=[],
                    headers=[], libraries=[{'type': 'guess', 'name': 'foo'}]):
        self.assertEqual(usage.include_path, include_path)
        self.assertEqual(usage.library_path, library_path)
        self.assertEqual(usage.headers, headers)
        self.assertEqual(usage.libraries, libraries)

    def test_basic(self):
        usage = self.make_usage('foo')
        self.check_usage(usage)
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['foo'],
        })

    def test_include_path(self):
        usage = self.make_usage('foo', include_path='include')
        self.check_usage(usage, include_path=['include'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': self.type, 'include_path': ['/srcdir/include'],
            'library_path': [], 'headers': [], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', include_path=['include'])
        self.check_usage(usage, include_path=['include'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': self.type, 'include_path': ['/srcdir/include'],
            'library_path': [], 'headers': [], 'libraries': ['foo'],
        })

    def test_include_path_absolute(self):
        usage = self.make_usage('foo', include_path='/path/to/include')
        self.check_usage(usage, include_path=['/path/to/include'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': self.type, 'include_path': ['/path/to/include'],
            'library_path': [], 'headers': [], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', include_path='/path/to/include')
        self.check_usage(usage, include_path=['/path/to/include'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': ['/path/to/include'],
            'library_path': [], 'headers': [], 'libraries': ['foo'],
        })

    def test_invalid_include_path(self):
        with self.assertRaises(FieldError):
            self.make_usage('foo', include_path='../include')

    def test_library_path(self):
        usage = self.make_usage('foo', library_path='lib')
        self.check_usage(usage, library_path=['lib'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': self.type, 'include_path': [],
            'library_path': ['/builddir/lib'], 'headers': [],
            'libraries': ['foo'],
        })

        usage = self.make_usage('foo', library_path=['lib'])
        self.check_usage(usage, library_path=['lib'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': self.type, 'include_path': [],
            'library_path': ['/builddir/lib'], 'headers': [],
            'libraries': ['foo'],
        })

    def test_library_path_absolute(self):
        usage = self.make_usage('foo', library_path='/path/to/lib')
        self.check_usage(usage, library_path=['/path/to/lib'])
        self.assertEqual(usage.get_usage(None, '/srcdir', '/builddir'), {
            'type': self.type, 'include_path': [],
            'library_path': ['/path/to/lib'], 'headers': [],
            'libraries': ['foo'],
        })

        usage = self.make_usage('foo', library_path='/path/to/lib')
        self.check_usage(usage, library_path=['/path/to/lib'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [],
            'library_path': ['/path/to/lib'], 'headers': [],
            'libraries': ['foo'],
        })

    def test_invalid_library_path(self):
        with self.assertRaises(FieldError):
            self.make_usage('foo', library_path='../lib')

    def test_headers(self):
        usage = self.make_usage('foo', headers='foo.hpp')
        self.check_usage(usage, headers=['foo.hpp'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': ['foo.hpp'], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', headers=['foo.hpp'])
        self.check_usage(usage, headers=['foo.hpp'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': ['foo.hpp'], 'libraries': ['foo'],
        })

    def test_libraries(self):
        usage = self.make_usage('foo', libraries='bar')
        self.check_usage(usage, libraries=['bar'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=['bar'])
        self.check_usage(usage, libraries=['bar'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=None)
        self.check_usage(usage, libraries=[])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': [],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'library', 'name': 'bar'},
        ])
        self.check_usage(usage, libraries=['bar'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'guess', 'name': 'bar'},
        ])
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'bar'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.check_usage(usage, libraries=[{'type': 'framework',
                                            'name': 'bar'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': [{'type': 'framework', 'name': 'bar'}],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.check_usage(usage, libraries=[])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['foo_sub'],
        })

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_required)
        self.check_usage(usage, libraries=['bar'])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['bar', 'foo_sub'],
        })

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['foo', 'foo_sub'],
        })

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_optional)
        self.check_usage(usage, libraries=['bar'])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['bar', 'foo_sub'],
        })

    def test_boost(self):
        submodules = {'names': '*', 'required': False}

        usage = self.make_usage('boost', submodules=submodules)
        self.check_usage(usage, headers=['boost/version.hpp'], libraries=[])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': ['boost/version.hpp'], 'libraries': [],
        })
        self.assertEqual(usage.get_usage(['thread'], None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': ['boost/version.hpp'], 'libraries': ['boost_thread'],
        })

        usage = self.make_usage('boost', libraries=['boost'],
                                submodules=submodules)
        self.check_usage(usage, headers=['boost/version.hpp'],
                         libraries=['boost'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': ['boost/version.hpp'], 'libraries': ['boost'],
        })
        self.assertEqual(usage.get_usage(['thread'], None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': ['boost/version.hpp'],
            'libraries': ['boost', 'boost_thread'],
        })

    def test_target_platform(self):
        usage = self.make_usage('gl', common_options={
            'target_platform': 'linux',
        })
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['GL'],
        })

        usage = self.make_usage('gl', common_options={
            'target_platform': 'darwin',
        })
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [],
            'libraries': [{'type': 'framework', 'name': 'OpenGL'}],
        })

        usage = self.make_usage('gl', libraries=['gl'], common_options={
            'target_platform': 'linux',
        })
        self.check_usage(usage, libraries=['gl'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['gl'],
        })

        usage = self.make_usage(
            'foo', libraries=[{'type': 'guess', 'name': 'gl'}],
            common_options={'target_platform': 'linux'}
        )
        self.check_usage(usage, libraries=[{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': self.type, 'include_path': [], 'library_path': [],
            'headers': [], 'libraries': ['GL'],
        })

    def test_invalid_usage(self):
        usage = self.make_usage('foo', include_path='include')
        with self.assertRaises(ValueError):
            usage.get_usage(None, None, None)

        usage = self.make_usage('foo', library_path='lib')
        with self.assertRaises(ValueError):
            usage.get_usage(None, None, None)


class TestSystem(TestPath):
    usage_type = SystemUsage
    type = 'system'
