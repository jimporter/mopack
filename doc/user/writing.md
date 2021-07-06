# Writing mopack.yml Configurations

## Your first configuration

The absolute simplest mopack configuration is an empty file, in which any
requested dependencies are assumed to be [system
dependencies](../reference/sources.md#system). However, that's not very
interesting. Instead, let's look at a basic `mopack.yml` configuration that
specifies a dependent package fetched and built from a tarball:

```yaml
packages:
  foo_pkg:
    source: tarball
    url: https://phobos.uac/foo_pkg-1.0.tar.gz
    build: bfg9000
```

This informs mopack that it should fetch a
[tarball](../reference/sources.md#tarball) from the specified URL and then build
it using the [bfg9000](../reference/builders.md#bfg9000) builder.

## Configuring builds/usage

In the above example, mopack builds `foo_pkg` using the default settings for
bfg9000. However, sometimes you may need to provide additional configuration
options for the build:

```yaml
packages:
  foo_pkg:
    source: tarball
    url: https://phobos.uac/foo_pkg-1.0.tar.gz
    build:
      type: bfg9000
      extra_args: --extra
    usage:
      type: pkg_config
      pcfile: foobar
```

Here, instead of a string for `build`, we specify a dictionary indicating the
type of the build and some extra arguments to be passed to it. Below, we'll show
a more complex example taking advantage of [variable
interpolation](#variable-interpolation).

We also explicitly specify a [*usage*](../reference/usage.md). A usage, as the
name implies, describes how a package should be *used*, e.g. where to find
header files, what libraries to link to, etc.

## Other package sources

One of the primary benefits of mopack is that packages can come from multiple
different origins, or sources. These include other source distributions similar
to [`tarball`](../reference/sources.md#tarball), such as
[`directory`](../reference/sources.md#directory) or
[`git`](../reference/sources.md#git), as well as full-fledged package managers
like [`apt`](../reference/sources.md#apt) or
[`conan`](../reference/sources.md#conan):

```yaml
packages:
  zlib:
    source: conan
    remote: zlib/1.2.11
```

## Project-wide options

In addition to specifying configuration options for a particular package, you
can also specify options for *all* packages, or all those of a particular type:

```yaml
options:
  target_platform: linux

  builders:
    bfg9000:
      toolchain: /path/to/toolchain.bfg
  sources:
    conan:
      build: missing

packages:
  # ...
```

This is especially useful for build system integration, e.g. for passing a
toolchain file set during configuration of the root project on to package
dependencies.

## Nested dependencies

When your project depends on a source distribution, that dependency might depend
on other packages in turn. mopack handles this automatically, and will add
nested dependencies to the list of packages to resolve. For example, if
`foo_pkg` [above](#your-first-configuration) contains a `mopack.yml` as follows,
then when we resolve our main `mopack.yml` configuration, `bar_pkg` will be
fetched and built so that `foo_pkg` can use it during its build:

```yaml
packages:
  bar_pkg:
    source: tarball
    url: https://phobos.uac/bar_pkg-2.0.tar.gz
    build: bfg9000
```

### Overriding nested dependencies

Sometimes, you may not want to use the nested dependencies as-is from other
packages. In this case, you can simply provide your own configuration in the
parent `mopack.yml`:

```yaml
packages:
  foo_pkg:
    source: tarball
    url: https://phobos.uac/foo_pkg-1.0.tar.gz
    build: bfg9000
  bar_pkg:
    source: tarball
    url: https://phobos.uac/bar_pkg-2.1.tar.gz
    build: bfg9000
```

When doing so, mopack will automatically determine the appropriate order to
build dependencies so that each package has all of its build requirements met.

!!! note
    In situations where one package depends on another, but the former package
    does *not* specify any mopack dependencies, you can ensure the correct build
    order by putting the inner dependency first in your `mopack.yml` file. Then,
    mopack will fetch and build that package first before proceeding to the next
    one.

### Exporting package configuration

When creating a source distribution package, you can make it easier to use this
package by exporting its configuration. This allows users of your package to
omit the details about how to build and use the package. For example, you can
include the following in your package's `mopack.yml` file:

```yaml
export:
  build: bfg9000
```

Then, users of your package can omit those fields from their configuration,
relying on mopack to fill in the blanks:

```yaml
packages:
  foo_pkg:
    source: tarball
    url: https://phobos.uac/foo_pkg-1.0.tar.gz
```

Of course, the parent configuration can still *override* the values set by a
dependency simply by including the appropriate configuration setting, as in our
[first example](#your-first-configuration).

## Variable interpolation

For more advanced scenarios, you can take advantage of variable interpolation to
programmatically specify package configurations. For example, suppose we wanted
to (partially) rewrite our [first configuration](#your-first-configuration)
using a [`custom`](../reference/builders.md#custom) builder:

```yaml
packages:
  foo_pkg:
    source: tarball
    url: https://phobos.uac/foo_pkg-1.0.tar.gz
    build:
      type: custom
      build_commands:
        - bfg9000 configure $builddir
        - cd $builddir
        - ninja
    usage: pkg_config
```

Here, `$builddir` represents a unique path for the current project that it can
use as a build directory. You can also spell this variable as `${{builddir}}`,
which can be useful if you need to append some alphanumeric characters to the
variable's value.

### Interpolating expressions

The above configuration works for building a package, but not for deploying it:
we haven't told the build system where to copy `foo_pkg`'s files. Here, we can
take advantage of expression interpolation to conditionally pass command line
arguments to bfg9000:

```yaml
packages:
  foo_pkg:
    source: tarball
    url: https://phobos.uac/foo_pkg-1.0.tar.gz
    build:
      type: custom
      build_commands:
        - >-
          bfg9000 configure $builddir ${{
            deploy_paths['prefix'] ? '--prefix=' + deploy_paths['prefix'] : ''
          }}
        - cd $builddir/.
        - ninja
      deploy_commands:
        - ninja install
    usage: pkg_config
```

### Conditional package specification

In some cases, a package's configuration should be *much* different depending on
the state of a variable, and the variable interpolation described above isn't
flexible enough to support this easily. To support this, a package's
configuration can be specified as a *list* of configurations with an added `if`
key to describe the conditions to use a particular configuration. Note that,
since `if` always takes an expression, the `$`/`${{ }}` sigil is not required:

```yaml
packages:
  foo_pkg:
    - if: host_platform == 'linux'
      source: apt
    - source: tarball
      url: https://phobos.uac/foo_pkg-1.0.tar.gz
      build: bfg9000
```

The conditional for each configuration is evaluated in turn, selecting the first
configuration where its conditional is true. If the last configuration has no
`if` key, it will always be selected as a last resort; otherwise, if no
conditional is satisfied, the package will be undefined.

## Submodules

In mopack, a "package" represents a single unit distributed in its most-typical
form. Thus Boost, despite containing a wide variety of libraries, is still a
single package. However, for a package like Boost, users rarely need to use the
*entirety* of the package. In this case, a package can be divided into
submodules. A submodule represents the smallest *usable* unit of a package; in
Boost's case, a single Boost library.

At its simplest, defining submodules for a package consists of listing the
available submodule names:

```yaml
packages:
  hello:
    source: tarball
    path: greeter-1.0.tar.gz
    build: bfg9000
    submodules: ['french', 'english']
```

This specifies a package with two submodules, *requiring* at least one to be
specified whenever [`mopack usage`](resolving.md#usage) is invoked.
