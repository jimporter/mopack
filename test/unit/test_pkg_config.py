import os
import re
from io import StringIO
from textwrap import dedent
from unittest import TestCase

from mopack.path import Path
from mopack.pkg_config import write_pkg_config
from mopack.placeholder import placeholder as ph
from mopack.shell import ShellArguments


class TestWritePkgConfig(TestCase):
    def _get_pkg_config(self, *args, **kwargs):
        out = StringIO()
        write_pkg_config(out, *args, **kwargs)
        # Skip the comment line at the top.
        return re.sub('.*\n\n', '', out.getvalue(), count=1)

    def test_default(self):
        cfg = self._get_pkg_config('mypackage')
        expected = dedent("""\
          Name: mypackage
          Description: mopack-generated package
          Version: 
        """)  # noqa: W291
        self.assertEqual(cfg, expected)

    def test_arguments(self):
        cfg = self._get_pkg_config(
            'mypackage', desc='my package', version='1.0',
            requires=['req1', 'req2'],
            cflags=ShellArguments(['-Ifoo', '-Ibar']),
            libs=ShellArguments(['-lfoo', '-lbar'])
        )
        expected = dedent("""\
          Name: mypackage
          Description: my package
          Version: 1.0
          Requires: req1 req2
          Cflags: -Ifoo -Ibar
          Libs: -lfoo -lbar
        """)
        self.assertEqual(cfg, expected)

    def test_empty_arguments(self):
        cfg = self._get_pkg_config(
            'mypackage', desc=None, version=None, requires=[],
            cflags=ShellArguments(), libs=ShellArguments()
        )
        expected = dedent("""\
          Name: mypackage
          Description: 
          Version: 
        """)  # noqa: W291
        self.assertEqual(cfg, expected)

    def test_spaces(self):
        cfg = self._get_pkg_config(
            'mypackage', desc='my package', version='1.0',
            requires=['req1', 'req2'],
            cflags=ShellArguments(['-Ifoo bar', '-Ibaz quux']),
            libs=ShellArguments(['-lfoo bar', '-lbaz quux'])
        )
        expected = dedent("""\
          Name: mypackage
          Description: my package
          Version: 1.0
          Requires: req1 req2
          Cflags: '-Ifoo bar' '-Ibaz quux'
          Libs: '-lfoo bar' '-lbaz quux'
        """)
        self.assertEqual(cfg, expected)

    def test_variables(self):
        cfg = self._get_pkg_config(
            'mypackage', desc='my package', version='1.0',
            cflags=ShellArguments(['-I' + ph(Path('foo', 'srcdir'))]),
            libs=ShellArguments(['-L' + ph(Path('', 'builddir')), '-lbar']),
            variables={'srcdir': '/srcdir', 'builddir': '/builddir',
                       'extra': None}
        )
        expected = dedent("""\
          srcdir=/srcdir
          builddir=/builddir

          Name: mypackage
          Description: my package
          Version: 1.0
          Cflags: '-I${{srcdir}}{sep}foo'
          Libs: '-L${{builddir}}' -lbar
        """).format(sep=os.sep)
        self.assertEqual(cfg, expected)

    def test_invalid(self):
        out = StringIO()
        with self.assertRaises(TypeError):
            write_pkg_config(out, 'mypackage', variables={'srcdir': 1})
        with self.assertRaises(TypeError):
            write_pkg_config(out, 'mypackage', cflags=1)
