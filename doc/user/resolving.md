# Resolving Packages With mopack

Most package managers allow developers to pull dependencies from a remote source
and prepare them for use by your build system. In this regard, mopack is no
different.

!!! note
    mopack is careful not to use the term "install"; depending on context,
    installation can refer to one of two very-different concepts:

    1. *Resolve*: to fetch a dependency from its origin and preparing it
       (usually by building) for use by the root project (e.g. `conan install`)
    2. *Deploy*: to copy any files from the dependency needed for running the
       root project into their final locations (e.g. `make install`)

## Resolution

The first step in working with dependencies is, unsurprisingly, getting them.
This is really two sub-steps rolled into one: fetching and building. This
typically involves downloading the appropriate files from some remote source
(possibly recursively in the case of [source
distributions](../reference/sources.md#source-distribution)) and then compiling
any projects as needed in the proper order, using their respective build
systems.

In most cases, this step should occur *before* configuration of the
root project's build (for build configuration systems that natively support
mopack, such as [bfg9000][bfg9000], this happens automatically). However, when
run manually, users should invoke the following command:

```sh
$ mopack resolve mopack.yml
```

This will get all the dependencies specified in `mopack.yml` and collect the
info necessary to use them in `mopack/`. If your build dir is *not* the current
directory, you can specify another location with
`--directory /path/to/builddir/`.

## Usage

Once a project's dependencies are ready to use, the next step is actually using
them. Generally, this step occurs *during* the root project's configuration
step. To get a package's usage information, run the following command:

```sh
$ mopack usage some-package
```

This will return the package's [usage](../reference/usage.md) information in
YAML format (or JSON if `--json` is passed), which can then be fed to the
dependent build steps.

## Deployment

Finally, some projects may want to deploy dependencies alongside the project's
own binaries (e.g. when running `make install`). This step (generally performed
during the root project's `make install` process, naturally) runs whatever
commands are necessary for each dependency to deploy them to the final
destination:

```sh
$ mopack deploy
```

Any dependency whose `deploy` property is true (the default) will then be
deployed.

[bfg9000]: https://jimporter.github.io/bfg9000/
