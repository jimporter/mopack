import os
import subprocess
from setuptools import setup, find_packages, Command

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

    def run(self):
        env = dict(os.environ)
        env.update({
            'COVERAGE_FILE': os.path.join(root_dir, '.coverage'),
            'COVERAGE_PROCESS_START': os.path.join(root_dir, '.coveragerc'),
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
    # XXX: When we add badges, be sure to strip them out here.
    long_desc = f.read()

try:
    import pypandoc
    long_desc = pypandoc.convert(long_desc, 'rst', format='md')
except ImportError:
    pass

setup(
    name='mopack',
    version='0.1.dev0',

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

    install_requires=['pyyaml', 'setuptools'],
    extras_require={
        'dev': ['coverage', 'flake8 >= 3.0', 'pypandoc'],
        'test': ['bfg9000', 'coverage', 'flake8 >= 3.0'],
    },

    entry_points={
        'console_scripts': [
            'mopack=mopack.driver:main'
        ],
        'mopack.sources': [
            'directory=mopack.sources.sdist:DirectoryPackage',
            'tarball=mopack.sources.sdist:TarballPackage',
        ],
        'mopack.builders': [
            'bfg9000=mopack.builders.bfg9000:Bfg9000Builder',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
)
