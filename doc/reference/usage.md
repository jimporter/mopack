# Usage

```yaml
packages:
  my_pkg:
    # ...
    usage:
      type: <usage-type>
      inherit_defaults: <boolean>
      submodule_map: <submodule-map>  # or...
      submodule_map:
        my_submodule: <submodule-map>
        '*': <submodule-map>
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
      pcfile: <string>  # system only
      dependencies: <dependency-list>
      include_path: <path-list>
      library_path: <path-list>
      headers: <header-list>
      libraries: <library-list>
      compile_flags: <shell-args>
      link_flags: <shell-args>
```

## pkg_config

```yaml
packages:
  my_pkg:
    # ...
    usage:
      type: pkg_config
      path: <path-list>
      pcfile: <string>
      extra_args: <shell-args>
```
