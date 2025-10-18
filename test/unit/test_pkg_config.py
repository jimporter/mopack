from io import StringIO
from unittest import TestCase

from mopack.path import Path
from mopack.pkg_config import write_pkg_config
from mopack.placeholder import placeholder as ph
from mopack.shell import ShellArguments


class TestWritePkgConfig(TestCase):
    def test_default(self):
        out = StringIO()
        write_pkg_config(out, 'mypackage')
        self.assertRegex(
            out.getvalue(),
            'Name: mypackage\n' +
            'Description: mopack-generated package\n' +
            'Version: \n$'
        )

    def test_arguments(self):
        out = StringIO()
        write_pkg_config(out, 'mypackage', desc='my package', version='1.0',
                         requires=['req1', 'req2'],
                         cflags=ShellArguments(['-Ifoo', '-Ibar']),
                         libs=ShellArguments(['-lfoo', '-lbar']))
        self.assertRegex(
            out.getvalue(),
            'Name: mypackage\n' +
            'Description: my package\n' +
            'Version: 1.0\n' +
            'Requires: req1 req2',
            'Cflags: -Ifoo -Ibar\n' +
            'Libs: -lfoo -lbar\n$'
        )

    def test_empty_arguments(self):
        out = StringIO()
        write_pkg_config(out, 'mypackage', desc=None, version=None,
                         requires=[], cflags=ShellArguments(),
                         libs=ShellArguments())
        self.assertRegex(
            out.getvalue(),
            'Name: mypackage\n' +
            'Description: \n' +
            'Version: \n$'
        )

    def test_variables(self):
        out = StringIO()
        write_pkg_config(
            out, 'mypackage', desc='my package', version='1.0',
            cflags=ShellArguments(['-I' + ph(Path('foo', 'srcdir'))]),
            libs=ShellArguments(['-L' + ph(Path('', 'builddir')), '-lbar']),
            variables={'srcdir': '/srcdir', 'builddir': '/builddir',
                       'extra': None}
        )
        self.assertRegex(
            out.getvalue(),
            'srcdir=/srcdir\n' +
            'builddir=/builddir\n\n' +
            'Name: mypackage\n' +
            'Description: my package\n' +
            'Version: 1.0\n' +
            'Cflags: -I[\'"]\\${srcdir}[/\\\\]foo[\'"]\n' +
            'Libs: -L[\'"]\\${builddir}[\'"] -lbar\n$'
        )

    def test_invalid(self):
        out = StringIO()
        with self.assertRaises(TypeError):
            write_pkg_config(out, 'mypackage', variables={'srcdir': 1})
        with self.assertRaises(TypeError):
            write_pkg_config(out, 'mypackage', cflags=1)
