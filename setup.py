import json
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

    def run(self):
        env = dict(os.environ)
        pythonpath = os.path.join(root_dir, 'test', 'scripts')
        if env.get('PYTHONPATH'):
            pythonpath += os.pathsep + env['PYTHONPATH']
        env.update({
            # Set the top srcdir so that our coverage configuration can find
            # the source files, even if we run `mopack` from another directory.
            'TOP_SRCDIR': root_dir,
            'PYTHONPATH': pythonpath,
            'COVERAGE_FILE': os.path.join(root_dir, '.coverage'),
            'COVERAGE_PROCESS_START': os.path.join(root_dir, 'setup.cfg'),
        })

        subprocess.run(['coverage', 'erase'], check=True)
        subprocess.run(
            ['coverage', 'run', 'setup.py', 'test'] +
            (['-q'] if self.verbose == 0 else []) +
            (['-s', self.test_suite] if self.test_suite else []),
            env=env, check=True
        )
        subprocess.run(['coverage', 'combine'], check=True,
                       stdout=subprocess.DEVNULL)


custom_cmds = {
    'coverage': Coverage,
}

try:
    from verspec.python import Version

    class DocServe(Command):
        description = 'serve the documentation locally'
        user_options = [
            ('working', 'w', 'use the documentation in the working directory'),
            ('dev-addr=', None, 'address to host the documentation on'),
        ]

        def initialize_options(self):
            self.working = False
            self.dev_addr = '0.0.0.0:8000'

        def finalize_options(self):
            pass

        def run(self):
            cmd = 'mkdocs' if self.working else 'mike'
            subprocess.run([
                cmd, 'serve', '--dev-addr=' + self.dev_addr
            ], check=True)

    class DocDeploy(Command):
        description = 'push the documentation to GitHub'
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            v = Version(version)
            alias = 'dev' if v.is_devrelease else 'latest'
            title = '{} ({})'.format(v.base_version, alias)
            short_version = '{}.{}'.format(*v.release[:2])

            try:
                info = json.loads(subprocess.run(
                    ['mike', 'list', '-j', alias], universal_newlines=True,
                    check=True, stdout=subprocess.PIPE
                ).stdout)
            except subprocess.CalledProcessError:
                info = None

            if info and info['version'] != short_version:
                t = re.sub(r' \({}\)$'.format(re.escape(alias)), '',
                           info['title'])
                subprocess.run(['mike', 'retitle', info['version'], t],
                               check=True)

            subprocess.run(['mike', 'deploy', '-ut', title, short_version,
                            alias], check=True)

    custom_cmds['doc_serve'] = DocServe
    custom_cmds['doc_deploy'] = DocDeploy
except ImportError:
    pass

with open(os.path.join(root_dir, 'README.md'), 'r') as f:
    # Read from the file and strip out the badges.
    long_desc = re.sub(r'(^# mopack)\n\n(.+\n)*', r'\1', f.read())

setup(
    name='mopack',
    version=version,

    description='A multiple-origin package manager',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    keywords='package manager',
    url='https://github.com/jimporter/mopack',

    author='Jim Porter',
    author_email='itsjimporter@gmail.com',
    license='BSD-3-Clause',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    packages=find_packages(exclude=['test', 'test.*']),
    package_data={'': ['defaults/*.yml']},

    install_requires=['colorama', 'pyparsing >= 3.0', 'pyyaml', 'setuptools'],
    extras_require={
        'dev': ['bfg9000', 'conan', 'coverage', 'flake8 >= 3.6',
                'flake8-quotes', 'mike >= 0.3.1', 'mkdocs-bootswatch-classic',
                'verspec', 'shtab'],
        'test': ['bfg9000', 'conan', 'coverage', 'flake8 >= 3.6',
                 'flake8-quotes', 'shtab'],
    },

    entry_points={
        'console_scripts': [
            'mopack=mopack.driver:main'
        ],
        'mopack.origins': [
            'apt=mopack.origins.apt:AptPackage',
            'conan=mopack.origins.conan:ConanPackage',
            'directory=mopack.origins.sdist:DirectoryPackage',
            'git=mopack.origins.sdist:GitPackage',
            'system=mopack.origins.system:SystemPackage',
            'tarball=mopack.origins.sdist:TarballPackage',
        ],
        'mopack.builders': [
            'bfg9000=mopack.builders.bfg9000:Bfg9000Builder',
            'cmake=mopack.builders.cmake:CMakeBuilder',
            'custom=mopack.builders.custom:CustomBuilder',
            'none=mopack.builders.none:NoneBuilder',
        ],
        'mopack.usage': [
            'path=mopack.usage.path_system:PathUsage',
            'pkg_config=mopack.usage.pkg_config:PkgConfigUsage',
            'system=mopack.usage.path_system:SystemUsage',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
)
