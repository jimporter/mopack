# Packages

Package configurations describe how to fetch a particular dependency as well as
all the necessary details to actually use it in the parent project.

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

`usage` <span class="subtitle">*optional, default*: *from builder*</span>
: The [usage](usage.md) to use when using this package. Some builders require
  this to be set, but others provide a default usage specification; the
  dependency can also define the usage in its `export` section.

### git

```yaml
packages:
  my_pkg:
    source: git
    repository: <url-or-path>
    tag: <tag-name>  # or...
    branch: <branch-name>  # or...
    commit: <commit-sha>
    srcdir: <inner-path>
    build: <build>
    usage: <usage>
```

`repository` <span class="subtitle">*required*</span>
: The URL or path to the repository.

`tag` <span class="subtitle">*optional*</span>
`branch`
`commit`
: The tag, branch, or commit to check out. At most one of these may be
  specified.

`srcdir` <span class="subtitle">*optional; default:* `.`</span>
: The directory within the repository containing the dependency's source code.

`build` <span class="subtitle">*required*</span>
: The [builder](builders.md) to use when resolving this package. Note that while
  this is required, it can be unset if the dependency defines the builder in its
  `export` section.

`usage` <span class="subtitle">*optional, default: from builder*</span>
: The [usage](usage.md) to use when using this package. Some builders require
  this to be set, but others provide a default usage specification; the
  dependency can also define the usage in its `export` section.

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

`path` <span class="subtitle">*required*</span>
`url`
: The path or URL to the archive. Exactly one of these must be specified.

`files` <span class="subtitle">*optional; default:* `null`</span>
: A glob or list of globs to filter the files extracted from the archive. If
  unspecified, extract everything.

`srcdir` <span class="subtitle">*optional; default:* `.`</span>
: The directory within the repository containing the dependency's source code.

`patch` <span class="subtitle">*optional; default:* `null`</span>
: The path to a patch file to apply to the extract source files.

`build` <span class="subtitle">*required*</span>
: The [builder](builders.md) to use when resolving this package. Note that while
  this is required, it can be unset if the dependency defines the builder in its
  `export` section.

`usage` <span class="subtitle">*optional, default: from builder*</span>
: The [usage](usage.md) to use when using this package. Some builders require
  this to be set, but others provide a default usage specification; the
  dependency can also define the usage in its `export` section.

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

`remote` <span class="subtitle">*optional; default:* `lib{package}-dev`</span>
: The Apt package(s) to fetch when resolving this package.

`repository` <span class="subtitle">*optional; default:* `null`</span>
: The Apt repository to fetch the package(s) from. If not specified, use the
  default repositories for the system.

`usage` <span class="subtitle">*optional, default:* [`system`](usage.md#system)</span>
: The [usage](usage.md) to use when using this package.

### conan

```yaml
options:
  sources:
    conan:
      build: <string-list>
      extra_args: <shell-args>
```

`build` <span class="subtitle">*optional; default:* `null`</span>
: A string (or list of strings) of packages that Conan should explicitly build.
  This corresponds to `--build={package}` on the `conan install` command line
  for each `{package}` in the list. You can also specify `all` to build
  *everything* (equivalent to `--build`).

`extra_args` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra arguments to pass to `conan install`. If a string is
  supplied, it will first be split according to POSIX shell rules.

```yaml
packages:
  my_pkg:
    source: conan
    remote: <string>
    build: <boolean>
    options:
      my_option: <string-or-boolean>
    usage: <usage>
```

`remote` <span class="subtitle">*required*</span>
: The specifier for the package in the Conan repository, e.g. `zlib/1.2.11`.

`build` <span class="subtitle">*optional; default:* `false`</span>
: True if the package should be built from source; false otherwise.

`options` <span class="subtitle">*optional; default:* `{}`</span>
: A dictionary of options to pass to Conan; for example, you could pass
  `shared: true` to request a shared library configuration.

`usage` <span class="subtitle">*optional, default:* [`pkg_config`](usage.md#pkg_config)</span>
: The [usage](usage.md) to use when using this package.

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
