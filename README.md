# mopack

[![Documentation][documentation-image]][documentation-link]
[![Build status][ci-image]][ci-link]
[![Coverage status][codecov-image]][codecov-link]

**mopack** (pronounced "ammopack" - name subject to change) is an experimental
*multiple origin* package manager, with an emphasis on C/C++ packages. It's
designed to allow users to resolve package dependencies from multiple package
managers ("origins").

## Design Goals

### No configuration necessary

By default, mopack will assume all package dependencies are already fetched
(downloaded and ready to use) and will attempt to resolve each dependency using
common methods for the relevant platform/runtime (e.g. pkg-config, searching
system paths).

### Builders can override developers

In typical usage, a project's developers will provide an mopack configuration to
make it easier for development builds to resolve dependencies. However, people
who *build* the project may prefer to resolve packages differently (e.g. if a
project defaults to resolving packages via Conan, someone building for `apt`
would likely override the config to point to `apt` packages).

## License

This project is licensed under the [BSD 3-clause license](LICENSE).

[documentation-image]: https://img.shields.io/badge/docs-mopack-blue.svg
[documentation-link]: https://jimporter.github.io/mopack/
[ci-image]: https://github.com/jimporter/mopack/workflows/build/badge.svg
[ci-link]: https://github.com/jimporter/mopack/actions?query=branch%3Amaster+workflow%3Abuild
[codecov-image]: https://codecov.io/gh/jimporter/mopack/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/jimporter/mopack
