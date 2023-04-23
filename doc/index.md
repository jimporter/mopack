# mopack

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

If you've downloaded mopack already, just run `pip install .` from the source
directory. (Equivalently, you can run `python setup.py install`.) From there,
you can start using mopack to build your software!

[setuptools]: https://pythonhosted.org/setuptools/
