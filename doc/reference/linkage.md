# Linkage

Linkage defines how to include a package in part of your build process. These
definitions are used to generate a [pkg-config][pkg-config] `.pc` file (or to
point to an existing one), which can then be used when compiling or linking
*your* project.

```yaml
packages:
  my_pkg:
    # ...
    linkage: <linkage_type>
    # or...
    linkage:
      type: <linkage_type>
      inherit_defaults: <boolean>
      submodule_linkage: <submodule_linkage>  # or...
      submodule_linkage:
        - if: <condition>
          <submodule_linkage>
        # ...
```

`type` <span class="subtitle">*required*</span>
: The type of linkage; see below for possible values.

`inherit_defaults` <span class="subtitle">*optional, default*: `false`</span>
: If true, inherit any unspecified values for this linkage from the defaults for
  the package. Defaults to false; however, any packages requested via `mopack
  linkage` but not defined will use the defaults.

`submodule_linkage` <span class="subtitle">*optional, default*: `null`</span>
: One or more configurations for submodule-specific linkage. Each element in the
  list may have an `if` field holding a boolean expression; mopack will use the
  first submodule linkage where the expression is true. See below for possible
  values for each linkage type.

### Linkage results

When calling `mopack linkage <dependency>`, mopack will provide information
about how to use that dependency in your project. At minimum, all dependencies
will report the following information:

```yaml
name: <string>
type: <linkage_type>
pcnames: <list[string]>
pkg_config_path: <list[path]>
```

`name`
: The name of the requested dependency.

`type`
: The type of linkage; see below for possible values.

`pcnames`
: A list of pkg-config `.pc` file names, without the `.pc` extension.

`pkg_config_path`
: A list of directories to add to pkg-config's search path to find the
  dependency's pkg-config `.pc` files.

## path/system { #path-system }

```yaml
packages:
  my_pkg:
    # ...
    linkage:
      type: path  # or ...
      type: system
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

`version` <span class="subtitle">*optional, default*: `null`</span>
: An optional version string, corresponding to the `Version` field of a
  pkg-config `.pc` file.

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
: A list of library files to link to when using this dependency. Each element
  can be a string, or an object of the form: `{type: <type>, name: <string>}`,
  where `<type>` is either `library` for ordinary libraries, or `framework` for
  macOS frameworks.

`compile_flags` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra flags to pass to the compiler when compiling with this
  dependency.

`link_flags` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra flags to pass to the linker when linking with this dependency.

```yaml
packages:
  my_pkg:
    # ...
    linkage:
      # ...
      submodule_linkage:
        - pcname: <string>  # system only
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
    linkage:
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
    linkage:
      # ...
      submodule_linkage:
        - pcname: <string>
```

`pcname` <span class="subtitle">*optional, default*: `{my_pkg}_{my_submodule}`</span>
: The name of the pkg-config `.pc` file for the submodule, without the
  extension.

[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
[msvc-comment-pragma]: https://learn.microsoft.com/en-us/cpp/preprocessor/comment-c-cpp
