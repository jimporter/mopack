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

## pkg-config

```yaml
packages:
  my_pkg:
    # ...
    usage:
      type: pkg-config
      path: <path>
      extra_args: <shell-args>
      submodule_map: <submodule-map>  # or...
      submodule_map:
        my_submodule: <submodule-map>
        '*': <submodule-map>
```
