# Builders

Builders define how [source distributions](packages.md#source-distributions)
should be built, allowing you to build dependencies from source even if they use
a different build system.

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
      extra_args: <shell_args>
```

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
      extra_args: <shell_args>
```

`extra_args` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra arguments to pass to `cmake`. If a string is
  supplied, it will first be split according to POSIX shell rules.

## custom

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: custom
      build_commands: <list[shell_args]>
      deploy_commands: <list[shell_args]>
```

`build_commands` <span class="subtitle">*optional, default*: `null`</span>
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
