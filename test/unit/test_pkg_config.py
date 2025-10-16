import os
import re
from io import StringIO
from unittest import TestCase

from mopack.path import Path
from mopack.pkg_config import write_pkg_config
from mopack.placeholder import placeholder as ph
from mopack.platforms import platform_name
from mopack.shell import ShellArguments


class TestWritePkgConfig(TestCase):
    quote = '"' if platform_name() == 'windows' else "'"

    def _get_pkg_config(self, *args, **kwargs):
        out = StringIO()
        write_pkg_config(out, *args, **kwargs)
        # Skip the comment line at the top.
        return re.sub('.*\n\n', '', out.getvalue(), count=1)

    def test_default(self):
        cfg = self._get_pkg_config('mypackage')
        self.assertEqual(
            cfg,
            'Name: mypackage\n' +
            'Description: mopack-generated package\n' +
            'Version: \n'
        )

    def test_arguments(self):
        cfg = self._get_pkg_config(
            'mypackage', desc='my package', version='1.0',
            requires=['req1', 'req2'],
            cflags=ShellArguments(['-Ifoo', '-Ibar']),
            libs=ShellArguments(['-lfoo', '-lbar'])
        )
        self.assertEqual(
            cfg,
            'Name: mypackage\n' +
            'Description: my package\n' +
            'Version: 1.0\n' +
            'Requires: req1 req2\n' +
            'Cflags: -Ifoo -Ibar\n' +
            'Libs: -lfoo -lbar\n'
        )

    def test_empty_arguments(self):
        cfg = self._get_pkg_config(
            'mypackage', desc=None, version=None, requires=[],
            cflags=ShellArguments(), libs=ShellArguments()
        )
        self.assertEqual(
            cfg,
            'Name: mypackage\n' +
            'Description: \n' +
            'Version: \n'
        )

    def test_spaces(self):
        cfg = self._get_pkg_config(
            'mypackage', desc='my package', version='1.0',
            requires=['req1', 'req2'],
            cflags=ShellArguments(['-Ifoo bar', '-Ibaz quux']),
            libs=ShellArguments(['-lfoo bar', '-lbaz quux'])
        )
        self.assertEqual(
            cfg,
            ('Name: mypackage\n' +
             'Description: my package\n' +
             'Version: 1.0\n' +
             'Requires: req1 req2\n' +
             'Cflags: {q}-Ifoo bar{q} {q}-Ibaz quux{q}\n' +
             'Libs: {q}-lfoo bar{q} {q}-lbaz quux{q}\n').format(q=self.quote)
        )

    def test_variables(self):
        cfg = self._get_pkg_config(
            'mypackage', desc='my package', version='1.0',
            cflags=ShellArguments(['-I' + ph(Path('foo', 'srcdir'))]),
            libs=ShellArguments(['-L' + ph(Path('', 'builddir')), '-lbar']),
            variables={'srcdir': '/srcdir', 'builddir': '/builddir',
                       'extra': None}
        )
        self.assertEqual(
            cfg,
            ('srcdir=/srcdir\n' +
             'builddir=/builddir\n\n' +
             'Name: mypackage\n' +
             'Description: my package\n' +
             'Version: 1.0\n' +
             'Cflags: -I{q}${{srcdir}}{sep}foo{q}\n' +
             'Libs: -L{q}${{builddir}}{q} -lbar\n').format(
                 q=self.quote, sep=os.sep
             )
        )

    def test_invalid(self):
        out = StringIO()
        with self.assertRaises(TypeError):
            write_pkg_config(out, 'mypackage', variables={'srcdir': 1})
        with self.assertRaises(TypeError):
            write_pkg_config(out, 'mypackage', cflags=1)
