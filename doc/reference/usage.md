# Usage

Usage defines how to include a package in part of your build process. These
definitions are used to generate a [pkg-config][pkg-config] `.pc` file (or to
point to an existing one), which can then be used when compiling or linking
*your* project.

```yaml
packages:
  my_pkg:
    # ...
    usage:
      type: <usage_type>
      inherit_defaults: <boolean>
      submodule_map: <submodule_map>  # or...
      submodule_map:
        my_submodule: <submodule_map>
        '*': <submodule_map>
```

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

`pcname` <span class="subtitle">*optional, default*: *package name*</span>
: The name of the pkg-config `.pc` file, without the extension. If
  [submodules](packages.md) are required for this package, this instead defaults
  to `null`.

`pkg_config_path` <span class="subtitle">*optional, default*: `null`</span>
: The path to look for the pkg-config file in. If not specified, use the default
  path for pkg-config.

```yaml
package:
  my_pkg:
    # ...
    usage:
      submodule_map:
        pcname: <string>
```

`pcname` <span class="subtitle">*optional, default*: `'{package}_{submodule}'`</span>
: The name of the pkg-config `.pc` file for the submodule, without the
  extension.

[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
