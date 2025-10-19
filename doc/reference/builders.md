# Builders

Builders define how [source distributions](packages.md#source-distributions)
should be built, allowing you to build dependencies from source even if they use
a different build system.

```yaml
packages:
  my_pkg:
    # ...
    build: <builder_type>
    # or...
    build:
      type: <builder_type>
      env: <env_vars>
```

`type` <span class="subtitle">*required*</span>
: The type of builder; see below for possible values.

`env` <span class="subtitle">*optional, default*: `{}`</span>
: A dictionary of environment variables to use when running any commands for
  this builder. This partially overrides any environment variables set
  [globally](file-structure.md#options) or for this
  [package](package.md#source-distributions).

## bfg9000

```yaml
options:
  builders:
    bfg9000:
      toolchain: <path>
```

`toolchain` <span class="subtitle">*optional, default*: `null`</span>
: The path to a bfg9000 toolchain file to use when building bfg-based
  dependencies.

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: bfg9000
      env: <env_vars>
      directory: <path>
      build: <boolean>
      extra_args: <shell_args>
```

`directory` <span class="subtitle">*optional, default*: *last directory*</span>
: The directory where the `build.bfg` file is located. By default, this is the
  last directory specified by the package configuration, usually `$srcdir`. (If
  a previous builder for this package defines a new directory, that will be used
  by default instead.)

`build` <span class="subtitle">*optional, default*: `true`</span>
: If true, automatically call [`ninja`][#ninja] to build the dependency after
  running `bfg9000 configure`.

`extra_args` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra arguments to pass to `bfg9000 configure`. If a string is
  supplied, it will first be split according to POSIX shell rules.

## cmake

```yaml
options:
  builders:
    cmake:
      toolchain: <path>
```

`toolchain` <span class="subtitle">*optional, default*: `null`</span>
: The path to a CMake toolchain file to use when building CMake-based
  dependencies.

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: cmake
      directory: <path>
      build: <boolean>
      extra_args: <shell_args>
```

`directory` <span class="subtitle">*optional, default*: *last directory*</span>
: The directory where the `CMakeLists.txt` file is located. By default, this is
  the last directory specified by the package configuration, usually `$srcdir`.
  (If a previous builder for this package defines a new directory, that will be
  used by default instead.)

`build` <span class="subtitle">*optional, default*: `true`</span>
: If true, automatically call [`ninja`][#ninja] to build the dependency after
  running `cmake`.

`extra_args` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra arguments to pass to `cmake`. If a string is supplied, it will
  first be split according to POSIX shell rules.

## ninja

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: ninja
      directory: <path>
      extra_args: <shell_args>
```

`directory` <span class="subtitle">*optional, default*: *last directory*</span>
: The directory where the `build.ninja` file is located. By default, this is
  the last directory specified by the package configuration, usually `$srcdir`.
  (If a previous builder for this package defines a new directory, that will be
  used by default instead.)

`extra_args` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra arguments to pass to `ninja`. If a string is
  supplied, it will first be split according to POSIX shell rules.

## custom

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: custom
      directory: <path>
      outdir: <symbol>
      build_commands: <list[shell_args]>
      deploy_commands: <list[shell_args]>
```

`directory` <span class="subtitle">*optional, default*: *last directory*</span>
: The directory where to run `build_commands` from. By default, this is the last
  directory specified by the package configuration, usually `$srcdir`. (If a
  previous builder for this package defines a new directory, that will be used
  by default instead.)

`outdir` <span class="subtitle">*optional, default*: `"build"`</span>
: The directory to use for files created by this builder. By default, this is
  the `build/` directory, and will be available in the rest of the configuration
  as the variable `$builddir`. If this is `null`, then there is no separate
  output directory. (Note that in a future revision, the default value
  will change to `null`.)

`build_commands` <span class="subtitle">*required*</span>
: A list of shell commands to execute when building the dependency. Each command
  can be a list of arguments or a single string (which will be split into
  arguments according to POSIX shell rules).

`deploy_commands` <span class="subtitle">*optional, default*: `null`</span>
: A list of shell commands to execute when deploying the dependency. Each
  command can be a list of arguments or a single string (which will be split
  into arguments according to POSIX shell rules).

## none

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: none
```
