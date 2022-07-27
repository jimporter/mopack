# Usage

Usage defines how to include a package in part of your build process. These
definitions are used to generate a [pkg-config][pkg-config] `.pc` file (or to
point to an existing one), which can then be used when compiling or linking
*your* project.

```yaml
packages:
  my_pkg:
    # ...
    usage: <usage_type>
    # or...
    usage:
      type: <usage_type>
      inherit_defaults: <boolean>
      submodule_map: <submodule_map>  # or...
      submodule_map:
        my_submodule: <submodule_map>
        '*': <submodule_map>
```

`type` <span class="subtitle">*required*</span>
: The type of usage; see below for possible values.

`inherit_defaults` <span class="subtitle">*optional, default*: `false`</span>
: If true, inherit any unspecified values for this usage from the defaults for
  the package. Defaults to false; however, any packages requested via `mopack
  usage` but not defined will use the defaults.

`submodule_map` <span class="subtitle">*optional, default*: `null`</span>
: A mapping from submodule names to submodule-specific configuration; a key of
  `'*'` refers to all submodules. See below for possible values for each usage
  type.

## path/system

```yaml
packages:
  my_pkg:
    # ...
    usage:
      type: path  # or ...
      type: system
      auto_link: <boolean>
      version: <string>
      pcname: <string>  # system only
      dependencies: <list[dependency]>
      include_path: <list[path]>
      library_path: <list[path]>
      headers: <list[header]>
      libraries: <list[library]>
      compile_flags: <shell_args>
      link_flags: <shell_args>
```

`auto_link` <span class="subtitle">*optional, default*: `false`</span>
: If true, the package requires a compiler that supports auto-link (e.g. MSVC).

`pcname` <span class="subtitle">*optional, default*: `{my_pkg}`</span>
: The name of the pkg-config `.pc` file, without the extension. If
  [submodules](packages.md) are *required* for this package, this instead
  defaults to `null`. If this file isn't found, use the other options to
  generate a pkg-config file.

`dependencies` <span class="subtitle">*optional, default*: `null`</span>
: A list of package dependencies that are required to use this package. This
  corresponds to the `Requires` field of a pkg-config `.pc` file.

`include_path` <span class="subtitle">*optional, default*: `null`</span>
: A list of paths to search for header files (as specified in `headers`). Any
  paths that include the required headers will be used when compiling with this
  dependency.

`library_path` <span class="subtitle">*optional, default*: `null`</span>
: A list of paths to search for library files (as specified in `libraries`). Any
  paths that include the required libraries will be used when linking with this
  dependency.

`headers` <span class="subtitle">*optional, default*: `null`</span>
: A list of headers that must be found when searching `include_path`. This can
  generally be a single representative header file to detect that the dependency
  could actually be found.

`libraries` <span class="subtitle">*optional, default*: `null`</span>
: A list of libary files to link to when using this dependency.

`compile_flags` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra flags to pass to the compiler when compiling with this
  dependency.

`link_flags` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra flags to pass to the linker when linking with this dependency.

```yaml
packages:
  my_pkg:
    # ...
    usage:
      # ...
      submodule_map:
        my_submodule:
          pcname: <string>  # system only
          dependencies: <list[dependency]>
          include_path: <list[path]>
          library_path: <list[path]>
          headers: <list[header]>
          libraries: <list[library]>
          compile_flags: <shell_args>
          link_flags: <shell_args>
```

`pcname` <span class="subtitle">*optional, default*: `{my_pkg}`</span>
: The name of the pkg-config `.pc` file, without the extension. If this file
  isn't found, use the other options to generate a pkg-config file.

`dependencies` <span class="subtitle">*optional, default*: `null`</span>
`include_path` <span class="subtitle">*optional, default*: `null`</span>
`library_path` <span class="subtitle">*optional, default*: `null`</span>
`headers` <span class="subtitle">*optional, default*: `null`</span>
`libraries` <span class="subtitle">*optional, default*: `null`</span>
`compile_flags` <span class="subtitle">*optional, default*: `null`</span>
`link_flags` <span class="subtitle">*optional, default*: `null`</span>
: As above.

## pkg_config

```yaml
packages:
  my_pkg:
    # ...
    usage:
      type: pkg_config
      pcname: <string>
      pkg_config_path: <list[path]>
```

`pcname` <span class="subtitle">*optional, default*: `{my_pkg}`</span>
: The name of the pkg-config `.pc` file, without the extension. If
  [submodules](packages.md) are *required* for this package, this instead
  defaults to `null`.

`pkg_config_path` <span class="subtitle">*optional, default*: `null`</span>
: The path to look for the pkg-config file in. If not specified, use the default
  path for pkg-config.

```yaml
packages:
  my_pkg:
    # ...
    usage:
      # ...
      submodule_map:
        my_submodule:
          pcname: <string>
```

`pcname` <span class="subtitle">*optional, default*: `{my_pkg}_{my_submodule}`</span>
: The name of the pkg-config `.pc` file for the submodule, without the
  extension.

[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
