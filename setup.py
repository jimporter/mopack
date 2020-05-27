import os
import re
import subprocess
from setuptools import setup, find_packages, Command

from mopack.app_version import version

root_dir = os.path.abspath(os.path.dirname(__file__))


class Coverage(Command):
    description = 'run tests with code coverage'
    user_options = [
        ('test-suite=', 's',
         "test suite to run (e.g. 'some_module.test_suite')"),
    ]

    def initialize_options(self):
        self.test_suite = None

    def finalize_options(self):
        pass

    def _make_subproc_rc(self):
        # For reasons I don't fully understand, coverage.py doesn't correctly
        # cover files in integration tests using our normal `.coveragerc`. To
        # fix this, change that line to `include = ${TOP}/mopack/*` so we get
        # full coverage. We don't do this universally, since using `source`
        # makes sure that if we run a subset of tests, coverage.py picks up
        # files with 0 coverage.
        with open(os.path.join(root_dir, '.coveragerc')) as f:
            rc = f.read()
        fixed = rc.replace('source = mopack', 'include = ${TOP}/mopack/*')

        result = os.path.join(root_dir, '.coveragerc-subproc')
        with open(result, 'w') as f:
            f.write(fixed)
        return result

    def run(self):
        env = dict(os.environ)
        pythonpath = os.path.join(root_dir, 'test', 'scripts')
        if env.get('PYTHONPATH'):
            pythonpath += os.pathsep + env['PYTHONPATH']
        env.update({
            'TOP': root_dir,
            'PYTHONPATH': pythonpath,
            'COVERAGE_FILE': os.path.join(root_dir, '.coverage'),
            'COVERAGE_PROCESS_START': self._make_subproc_rc(),
        })

        subprocess.check_call(['coverage', 'erase'])
        subprocess.check_call(
            ['coverage', 'run', 'setup.py', 'test'] +
            (['-q'] if self.verbose == 0 else []) +
            (['-s', self.test_suite] if self.test_suite else []),
            env=env
        )
        subprocess.check_call(['coverage', 'combine'])


custom_cmds = {
    'coverage': Coverage,
}

try:
    from flake8.main.setuptools_command import Flake8

    class LintCommand(Flake8):
        def distribution_files(self):
            return ['setup.py', 'mopack', 'test']

    custom_cmds['lint'] = LintCommand
except ImportError:
    pass

with open(os.path.join(root_dir, 'README.md'), 'r') as f:
    # Read from the file and strip out the badges.
    long_desc = re.sub(r'(^# mopack)\n\n(.+\n)*', r'\1', f.read())

try:
    import pypandoc
    long_desc = pypandoc.convert(long_desc, 'rst', format='md')
except ImportError:
    pass

setup(
    name='mopack',
    version=version,

    description='A multiple-origin package manager',
    long_description=long_desc,
    keywords='package manager',
    url='https://github.com/jimporter/mopack',

    author='Jim Porter',
    author_email='itsjimporter@gmail.com',
    license='BSD',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    packages=find_packages(exclude=['test', 'test.*']),

    install_requires=['colorama', 'pyyaml', 'setuptools'],
    extras_require={
        'dev': ['bfg9000', 'conan', 'coverage', 'flake8 >= 3.6', 'pypandoc'],
        'test': ['bfg9000', 'conan', 'coverage', 'flake8 >= 3.6'],
    },

    entry_points={
        'console_scripts': [
            'mopack=mopack.driver:main'
        ],
        'mopack.sources': [
            'apt=mopack.sources.apt:AptPackage',
            'conan=mopack.sources.conan:ConanPackage',
            'directory=mopack.sources.sdist:DirectoryPackage',
            'system=mopack.sources.system:SystemPackage',
            'tarball=mopack.sources.sdist:TarballPackage',
        ],
        'mopack.builders': [
            'bfg9000=mopack.builders.bfg9000:Bfg9000Builder',
            'cmake=mopack.builders.cmake:CMakeBuilder',
        ],
        'mopack.usage': [
            'pkg-config=mopack.usage.pkg_config:PkgConfigUsage',
            'path=mopack.usage.path_system:PathUsage',
            'system=mopack.usage.path_system:SystemUsage',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
)
