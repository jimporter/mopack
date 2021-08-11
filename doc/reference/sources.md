# Package Sources

## Source distributions

### directory

```yaml
packages:
  my_pkg:
    source: directory
    version: <string>
    path: <path>
    build: <build>
    usage: <usage>
```

### git

```yaml
packages:
  my_pkg:
    source: git
    tag: <tag-name>  # or...
    branch: <branch-name>  # or...
    commit: <commit-sha>
    srcdir: <inner-path>
    build: <build>
    usage: <usage>
```

### tarball

```yaml
packages:
  my_pkg:
    source: tarball
    path: <path>  # or...
    url: <url>
    files: <glob-list>
    srcdir: <inner-path>
    patch: <path>
    build: <build>
    usage: <usage>
```

## Other sources

### apt

```yaml
packages:
  my_pkg:
    source: apt
    remote: <string-list>
    repository: <string>
    usage: <usage>
```

### conan

```yaml
options:
  sources:
    conan:
      build: <string-list>
      extra_args: <shell-args>
packages:
  my_pkg:
    source: conan
    remote: <string>
    build: <boolean>
    options:
      my_option: <string-or-boolean>
    usage: <usage>
```

### system

```yaml
packages:
  my_pkg:
    source: system
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
