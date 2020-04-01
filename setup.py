from setuptools import setup, find_packages

custom_cmds = {}

try:
    from flake8.main.setuptools_command import Flake8

    class LintCommand(Flake8):
        def distribution_files(self):
            return ['setup.py', 'mopack']

    custom_cmds['lint'] = LintCommand
except ImportError:
    pass

setup(
    name='mopack',
    version='0.1.dev0',

    description='A multiple-origin package manager',
    # long_description=...,
    keywords='package manager',
    # url=...,

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
        'test': ['flake8 >= 3.0'],
    },

    entry_points={
        'console_scripts': [
            'mopack=mopack.driver:main'
        ],
        'mopack.sources': [
            'tarball=mopack.sources.tarball:TarballPackage',
        ],
        'mopack.builders': [
            'bfg9000=mopack.builders.bfg9000:Bfg9000Builder',
        ],
    },

    cmdclass=custom_cmds,
)
