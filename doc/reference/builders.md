# Builders

Builders define how [source distributions](sources.md#source-distributions)
should be built, allowing you to build dependencies from source even if they use
a different build system.

## bfg9000

```yaml
options:
  builders:
    bfg9000:
      toolchain: <path>
packages:
  my_pkg:
    # ...
    builder:
      type: bfg9000
      extra_args: <shell-args>
```

## cmake

```yaml
options:
  builders:
    cmake:
      toolchain: <path>
packages:
  my_pkg:
    # ...
    builder:
      type: cmake
      extra_args: <shell-args>
```

## custom

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: custom
      build_commands: <shell-args-list>
      deploy_commands: <shell-args-list>
```

## none

```yaml
packages:
  my_pkg:
    # ...
    builder:
      type: none
```
