# File Structure

Mopack files are structured into three main sections: [packages](#packages),
which list the package dependencies and how to resolve them;
[options](#options), which define various cross-package settings; and
[exports](#exports), which tell other packages how to use the current one.

## Exports

The export section allows a package to declare how *other* packages should use
it as a dependency, when used as a [source
distribution](packages.md#source-distributions).

```yaml
export:
  submodules: <submodules>
  build: <build>
  usage: <usage>
```

`submodules` <span class="subtitle">*optional, default*: `null`</span>
: A list of available submodules, or `*` to indicate that any submodule name
  should be accepted. If this is specified, using this package via `mopack
  usage` *must* specify a submodule. To declare that submodules are optional for
  usage, you can specify a dictionary:

        submodules:
          names: <submodules>
          required: false

`build` <span class="subtitle">*optional, default:* `null`</span>
: The [builder](builders.md) to use when resolving this package. If unspecified,
  other packages using this one will have to define the `build` in their own
  mopack configuration.

`usage` <span class="subtitle">*optional, default*: *from builder*</span>
: The [usage](usage.md) to use when using this package. Some builders require
  this to be set, but others provide a default usage specification; if
  unspecified and the builder requires this to be set, then other packages using
  this one will need to define it.

## Options

```yaml
options:
  target_platform: <platform>
  env: <dict>
  deploy_paths: <dict>

  sources:  # ...
  builders:  # ...
```

## Packages

```yaml
packages:
  my_pkg:
    source: <source>
    # ...
```

## Expression Syntax
