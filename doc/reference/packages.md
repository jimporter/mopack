# Packages

Package configurations describe how to fetch a particular dependency as well as
all the necessary details to actually use it in the parent project.

```yaml
packages:
  my_pkg:
    origin: <package_origin>
    inherit_defaults: <boolean>
    deploy: <boolean>
    submodules: <submodules>
```

`origin` <span class="subtitle">*required*</span>
: The type of dependency, corresponding to a particular origin (e.g. a package
  manager); see below for possible values.

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

  This can also be set in a package's [`export`](file-structure.md#exports)
  section.

## Source distributions

### directory

```yaml
packages:
  my_pkg:
    origin: directory
    path: <path>
    build: <build>
    usage: <usage>
```

`path` <span class="subtitle">*required*</span>
: The path to the source directory of the dependency.

`build` <span class="subtitle">*required*</span>
: The [builder](builders.md) to use when resolving this package. Note that while
  this is required, it can be unset if the dependency defines the builder in its
  [`export`](file-structure.md#exports) section.

`usage` <span class="subtitle">*optional, default*: *from builder*</span>
: The [usage](usage.md) to use when using this package. Some builders require
  this to be set, but others provide a default usage specification; the
  dependency can also define the usage in its
  [`export`](file-structure.md#exports) section.

### git

```yaml
packages:
  my_pkg:
    origin: git
    repository: <url | path>
    tag: <tag_name>  # or...
    branch: <branch_name>  # or...
    commit: <commit_sha>
    srcdir: <inner_path>
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
    origin: tarball
    path: <path>  # or...
    url: <url>
    files: <list[glob]>
    srcdir: <inner_path>
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

## Other origins

### apt

```yaml
packages:
  my_pkg:
    origin: apt
    remote: <list[string]>
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
  origins:
    conan:
      build: <list[string]>
      extra_args: <shell_args>
```

`build` <span class="subtitle">*optional; default:* `null`</span>
: A string (or list of strings) of packages that Conan should explicitly build.
  This corresponds to `--build={package}` on the `conan install` command line
  for each `{package}` in the list. You can also specify `all` to build
  *everything* (equivalent to `--build`).

`extra_args` <span class="subtitle">*optional, default*: `null`</span>
: A list of extra arguments to pass to `conan install`. If a string is supplied,
  it will first be split according to POSIX shell rules.

```yaml
packages:
  my_pkg:
    origin: conan
    remote: <string>
    build: <boolean>
    options:
      my_option: <string | boolean>
    usage: <usage>
```

`remote` <span class="subtitle">*required*</span>
: The specifier for the package in the Conan repository, e.g. `zlib/1.2.12`.

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
    origin: system
    auto_link: <boolean>
    version: <string>
    pcname: <string>
    dependencies: <list[dependency]>
    include_path: <list[path]>
    library_path: <list[path]>
    headers: <list[header]>
    libraries: <list[library]>
    compile_flags: <shell_args>
    link_flags: <shell_args>
    submodule_map: <submodule_map>  # or...
    submodule_map:
      my_submodule: <submodule_map>
      '*': <submodule_map>
```

`auto_link` <span class="subtitle">*optional, default*: `false`</span>
`version` <span class="subtitle">*optional, default*: `null`</span>
`pcname` <span class="subtitle">*optional, default*: `{my_pkg}`</span>
`dependencies` <span class="subtitle">*optional, default*: `null`</span>
`include_path` <span class="subtitle">*optional, default*: `null`</span>
`library_path` <span class="subtitle">*optional, default*: `null`</span>
`headers` <span class="subtitle">*optional, default*: `null`</span>
`libraries` <span class="subtitle">*optional, default*: `null`</span>
`compile_flags` <span class="subtitle">*optional, default*: `null`</span>
`link_flags` <span class="subtitle">*optional, default*: `null`</span>
: See [`system`](usage.md#pathsystem) usage.
