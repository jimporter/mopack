# Package Sources

Package sources describe how to fetch a particular package as well as all the
necessary details to actually use it as a dependency.

```yaml
packages:
  my_pkg:
    source: <package-source>
    inherit_defaults: <boolean>
    deploy: <boolean>
    submodules: <submodules>
```

`source` <span class="subtitle">*required*</span>
: The type of dependency, corresponding to a particular origin (e.g. a
  package manager); see below for possible values.

`inherit_defaults` <span class="subtitle">*optional, default*: `false`</span>
: If true, inherit any unspecified values for this dependency from the defaults
  for the package. Defaults to false; however, any packages requested via
  `mopack usage` but not defined will use the defaults.

`deploy` <span class="subtitle">*optional, default*: `true`</span>
: If true, deploy this package when calling `mopack deploy`.

`submodules` <span class="subtitle">*optional, default*: `null`</span>
: A list of available submodules, or `*` to indicate that any submodule name
  should be accepted. If this is specified, using this package via `mopack
  usage` *must* specify a submodule. To declare that submodules are optional for
  usage, you can specify a dictionary:

        submodules:
          names: <submodules>
          required: false

## Source distributions

### directory

```yaml
packages:
  my_pkg:
    source: directory
    path: <path>
    build: <build>
    usage: <usage>
```

`path` <span class="subtitle">*required*</span>
: The path to the source directory of the dependency.

`build` <span class="subtitle">*required*</span>
: The [builder](builders.md) to use when resolving this package. Note that while
  this is required, it can be unset if the dependency defines the builder in its
  `export` section.

`usage` <span class="subtitle">*optional, default: from builder*</span>
: The [usage](usage.md) to use when, well, using this package. Some builders
  require this to be set, but others provide a default usage specification; the
  dependency can also define the usage in its `export` section.

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
    pcname: <string>
    dependencies: <dependency-list>
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
