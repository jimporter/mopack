# File Structure

Mopack files are structured into three main sections: [packages](#packages),
which list the package dependencies and how to resolve them;
[options](#options), which define various cross-package settings; and
[exports](#exports), which tell other packages how to use the current one.

## Exports

The `export` section allows a package to declare how *other* packages should use
it as a dependency, when used as a [source
distribution](packages.md#source-distributions).

```yaml
export:
  submodules: <submodules>
  build: <build>
  linkage: <linkage>
```

`submodules` <span class="subtitle">*optional, default*: `null`</span>
: A list of available submodules, or `*` to indicate that any submodule name
  should be accepted. If this is specified, using this package via `mopack
  linkage` *must* specify a submodule. To declare that submodules are optional
  for linkage, you can specify a dictionary:

        submodules:
          names: <submodules>
          required: false

`build` <span class="subtitle">*optional, default:* `null`</span>
: The [builder](builders.md) to use when resolving this package. If unspecified,
  other packages using this one will have to define the `build` in their own
  mopack configuration.

`linkage` <span class="subtitle">*optional, default*: *from builder*</span>
: The [linkage](linkage.md) to use when using this package. Some builders
  require this to be set, but others provide a default linkage specification; if
  unspecified and the builder requires this to be set, then other packages using
  this one will need to define it.

## Options

The `options` section lets you specify project-wide options to configure *all*
your dependencies, or all of those with a particular origin or builder.

```yaml
options:
  target_platform: <platform>
  env: <dict>
  deploy_dirs: <dict>

  origins:  # ...
  builders:  # ...
```

`target_platform` <span class="subtitle">*optional, default*: *host platform*</span>
: The target platform to build for. This is useful for cross-compilation.
  Examples of target platforms include: `linux`, `windows`, or `darwin` (macOS).

`env` <span class="subtitle">*optional, default:* `null`</span>
: A dictionary of environment variables and their values to set while resolving
  dependencies. These override current environment variables of the same name
  (e.g. from the shell).

`deploy_dirs` <span class="subtitle">*optional, default:* `null`</span>
: A dictionary mapping *kinds* of deploy directories to their actual locations.
  Each kind should be one of the [GNU directory variables][gnu-directory-vars].
  At the simplest, you can just specify the `prefix` variable. Note: the exact
  kinds that are supported depend on the package origin and builder.

`origins` <span class="subtitle">*optional, default:* `null`</span>
: A dictionary of options for specific [package origins](packages.md).

`builders` <span class="subtitle">*optional, default:* `null`</span>
: A dictionary of options for specific [package builders](builders.md).

## Packages

The `packages` section lists all the [package dependencies](packages.md) for
your project, as well as how to resolve them. Packages are specified as a
dictionary mapping package names to their configurations:

```yaml
packages:
  my_pkg:
    origin: <origin>
    # ...
```

### Conditional package definitions

You can also specify a list of configurations for a given package; in addition
to the usual properties, each element of the list (except the last) must have an
`if` property. mopack will then use the first configuration whose conditional is
satisfied:

```yaml
packages:
  my_pkg:
    - if: <condition>
      origin: <origin>
      # ...
    - origin: <origin>
      # ...
```

Conditionals use mopack's [expression syntax](expressions.md), though unlike in
other contexts, the `${}` sigil isn't required:

```yaml
packages:
  my_pkg:
    - if: target_platform == 'linux'
      # ...
```

[gnu-directory-vars]: https://www.gnu.org/prep/standards/html_node/Directory-Variables.html
