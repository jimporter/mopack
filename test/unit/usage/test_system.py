from . import UsageTest

from mopack.usage.system import SystemUsage


class TestSystem(UsageTest):
    usage_type = SystemUsage

    def test_basic(self):
        usage = self.make_usage('foo')
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['foo'],
        })

    def test_headers(self):
        usage = self.make_usage('foo', headers='foo.hpp')
        self.assertEqual(usage.headers, ['foo.hpp'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': ['foo.hpp'], 'libraries': ['foo'],
        })

        usage = self.make_usage('foo', headers=['foo.hpp'])
        self.assertEqual(usage.headers, ['foo.hpp'])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'foo'}])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': ['foo.hpp'], 'libraries': ['foo'],
        })

    def test_libraries(self):
        usage = self.make_usage('foo', libraries='bar')
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=['bar'])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=None)
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': [],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'library', 'name': 'bar'},
        ])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['bar'])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'guess', 'name': 'bar'},
        ])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'bar'}])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['bar'],
        })

        usage = self.make_usage('foo', libraries=[
            {'type': 'framework', 'name': 'bar'},
        ])
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [
            {'type': 'framework', 'name': 'bar'},
        ])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': [
                {'type': 'framework', 'name': 'bar'},
            ],
        })

    def test_target_platform(self):
        usage = self.make_usage('gl', general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['GL'],
        })

        usage = self.make_usage('gl', general_options={
            'target_platform': 'darwin',
        })
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': [
                {'type': 'framework', 'name': 'OpenGL'},
            ],
        })

        usage = self.make_usage('gl', libraries=['gl'], general_options={
            'target_platform': 'linux',
        })
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, ['gl'])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['gl'],
        })

        usage = self.make_usage(
            'foo', libraries=[{'type': 'guess', 'name': 'gl'}],
            general_options={'target_platform': 'linux'}
        )
        self.assertEqual(usage.headers, [])
        self.assertEqual(usage.libraries, [{'type': 'guess', 'name': 'gl'}])
        self.assertEqual(usage.usage(None, None), {
            'type': 'system', 'headers': [], 'libraries': ['GL'],
        })
