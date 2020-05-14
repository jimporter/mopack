import ntpath
import posixpath
from unittest import mock, TestCase

from mopack.types import *


class TestInnerPath(TestCase):
    def test_valid(self):
        self.assertEqual(inner_path('field', 'path'), 'path')
        self.assertEqual(inner_path('field', 'path/..'), '.')
        self.assertEqual(inner_path('field', 'foo/../bar'), 'bar')

    def test_outer(self):
        self.assertRaises(FieldError, inner_path, 'field', '../path')
        self.assertRaises(FieldError, inner_path, 'field', 'path/../..')

    def test_absolute_posix(self):
        with mock.patch('os.path', posixpath):
            self.assertRaises(FieldError, inner_path, 'field', '/path')

    def test_absolute_nt(self):
        with mock.patch('os.path', ntpath):
            self.assertRaises(FieldError, inner_path, 'field', '/path')
            self.assertRaises(FieldError, inner_path, 'field', 'C:path')
            self.assertRaises(FieldError, inner_path, 'field', 'C:\\path')
            self.assertRaises(FieldError, inner_path, 'field', 'C:')


class TestShellArgs(TestCase):
    def test_single(self):
        self.assertEqual(shell_args()('field', 'foo'), ['foo'])

    def test_multiple(self):
        self.assertEqual(shell_args()('field', 'foo bar baz'),
                         ['foo', 'bar', 'baz'])

    def test_quote(self):
        self.assertEqual(shell_args()('field', 'foo "bar baz"'),
                         ['foo', 'bar baz'])
        self.assertEqual(shell_args()('field', 'foo"bar baz"'), ['foobar baz'])

    def test_type(self):
        self.assertEqual(shell_args(type=tuple)('field', 'foo bar baz'),
                         ('foo', 'bar', 'baz'))

    def test_escapes(self):
        self.assertEqual(shell_args()('field', 'foo\\ bar'), ['foo\\', 'bar'])
        self.assertEqual(shell_args(escapes=True)('field', 'foo\\ bar'),
                         ['foo bar'])

    def test_invalid(self):
        self.assertRaises(FieldError, shell_args(), 'field', 1)
