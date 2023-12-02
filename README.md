# mopack

[![PyPi version][pypi-image]][pypi-link]
[![Documentation][documentation-image]][documentation-link]
[![Build status][ci-image]][ci-link]
[![Coverage status][codecov-image]][codecov-link]

**mopack** (pronounced "ammopack") is a *multiple origin* package manager, with
an emphasis on C/C++ packages. It's designed to allow users to resolve package
dependencies from multiple package managers ("origins").

## Why mopack?

### Separate abstract and concrete dependencies

Generally speaking, developers of a project are more concerned about
dependencies in the abstract: if your project requires Boost v1.50+, that's all
that really matters. However, when building a project, you work with concrete
dependencies: you naturally have to download a particular version of Boost and
build/install it in a particular way. mopack supports this by letting a
project's build system asking how to use (link to) an abstract dependency, which
mopack will resolve via a particular concrete dependency.

### No configuration necessary

If you've already downloaded and installed a project's dependencies, you usually
don't need to do anything else. mopack can find dependencies using common
methods for the relevant platform (e.g. pkg-config, searching system paths).

### Easy overrides

To simplify building their project, developers can provide a default mopack
configuration so that a standard build just works without any extra effort.
However, people who *build* the project may prefer to resolve packages from
somewhere else. mopack makes this easy: simply pass in an extra mopack file with
new definitions for any dependency, and mopack will use those instead.

## Installation

mopack uses [setuptools][setuptools], so installation is much the same as any
other Python package:

```sh
$ pip install mopack
```

From there, you can start using mopack to build your software!

## License

This project is licensed under the [BSD 3-clause license](LICENSE).

[pypi-image]: https://img.shields.io/pypi/v/mopack.svg
[pypi-link]: https://pypi.python.org/pypi/mopack
[documentation-image]: https://img.shields.io/badge/docs-mopack-blue.svg
[documentation-link]: https://jimporter.github.io/mopack/
[ci-image]: https://github.com/jimporter/mopack/actions/workflows/build.yml/badge.svg
[ci-link]: https://github.com/jimporter/mopack/actions/workflows/build.yml?query=branch%3Amaster
[codecov-image]: https://codecov.io/gh/jimporter/mopack/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/jimporter/mopack
[setuptools]: https://pythonhosted.org/setuptools/
