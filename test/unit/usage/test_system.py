from . import UsageTest

from mopack.usage.system import SystemUsage


class TestSystem(UsageTest):
    usage_type = SystemUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['foo'],
        })

    def test_headers(self):
        usage = self.make_usage('foo', headers='foo.hpp')
        self.assertEqual(usage.headers, ['foo.hpp'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': ['foo.hpp'], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', headers=['foo.hpp'])
        self.assertEqual(usage.headers, ['foo.hpp'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': ['foo.hpp'], 'libraries': ['foo'],
        })

    def test_libraries(self):
        usage = self.make_usage('foo', libraries='bar')
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=['bar'])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=None)
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': [],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'library', 'name': 'bar'},
        ])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'guess', 'name': 'bar'},
        ])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'bar'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [
            {'type': 'framework', 'name': 'bar'},
        ])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': [
                {'type': 'framework', 'name': 'bar'},
            ],
        })

    def test_submodules(self):
        submodules_required = {'names': '*', 'required': True}
        submodules_optional = {'names': '*', 'required': False}

        usage = self.make_usage('foo', submodules=submodules_required)
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': 'system', 'headers': [], 'libraries': ['foo_sub'],
        })

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_required)
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar', 'foo_sub'],
        })

        usage = self.make_usage('foo', submodules=submodules_optional)
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': 'system', 'headers': [], 'libraries': ['foo', 'foo_sub'],
        })

        usage = self.make_usage('foo', libraries=['bar'],
                                submodules=submodules_optional)
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.get_usage(['sub'], None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar', 'foo_sub'],
        })

    def test_boost(self):
        submodules = {'names': '*', 'required': False}

        usage = self.make_usage('boost', submodules=submodules)
        self.assertEqual(usage.headers, ['boost/version.hpp'])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': ['boost/version.hpp'],
            'libraries': [],
        })
        self.assertEqual(usage.get_usage(['thread'], None, None), {
            'type': 'system', 'headers': ['boost/version.hpp'],
            'libraries': ['boost_thread'],
        })

        usage = self.make_usage('boost', headers=None, libraries=['boost'],
                                submodules=submodules)
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['boost'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['boost'],
        })
        self.assertEqual(usage.get_usage(['thread'], None, None), {
            'type': 'system', 'headers': [],
            'libraries': ['boost', 'boost_thread'],
        })

    def test_target_platform(self):
        usage = self.make_usage('gl', general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['GL'],
        })

        usage = self.make_usage('gl', general_options={
            'target_platform': 'darwin',
        })
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': [
                {'type': 'framework', 'name': 'OpenGL'},
            ],
        })

        usage = self.make_usage('gl', libraries=['gl'], general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['gl'])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['gl'],
        })

        usage = self.make_usage(
            'foo', libraries=[{'type': 'guess', 'name': 'gl'}],
            general_options={'target_platform': 'linux'}
        )
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.get_usage(None, None, None), {
            'type': 'system', 'headers': [], 'libraries': ['GL'],
        })
