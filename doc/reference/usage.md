# Usage

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
      include_path: <path-list>
      library_path: <path-list>
      headers: <header-list>
      libraries: <library-list>
      compile_flags: <shell-args>
      link_flags: <shell-args>
      submodule_map: <submodule-map>  # or...
      submodule_map:
        my_submodule: <submodule-map>
        '*': <submodule-map>
```

## pkg_config

```yaml
packages:
  my_pkg:
    # ...
    usage:
      type: pkg_config
      path: <path-list>
      extra_args: <shell-args>
      submodule_map: <submodule-map>  # or...
      submodule_map:
        my_submodule: <submodule-map>
        '*': <submodule-map>
```