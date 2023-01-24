# Expressions

Sometimes, how a dependency should be resolved depends on the system you're
using. For example, you would only use [apt](packages.md#apt) dependencies on
Linux systems. To support this, mopack lets you write your dependency
configurations using expressions.

## Introducing expressions

You can introduce expressions with `${{ ... }}`, or `$` if the expression is
just a variable name:

```yaml
packages:
  my_pkg:
    # ...
    build:
      type: custom
      build_commands:
        - ./configure --prefix=${{ deploy_dirs['prefix'] }}
    usage:
      type: path
      # ...
      compile_flags: -I$srcdir/include
```

When defining the expression for [conditional package
definitions](file-structure.md#conditional-package-definitions), this introducer
isn't necessary (a conditional is always an expression to begin with):

```yaml
packages:
  hello:
    - if: host_platform == 'linux'
      source: apt
      # ...
    - source: tarball
      # ...
```

## Literals

Within expressions, you can use a variety of literal types:

* booleans (`true` or `false`)
* null values (`null`)
* integers (decimal digits, possibly preceded by `-`)
* strings (quoted using either `'` or `"`, and with `\` for escapes)
* arrays (`[value, ...]`)

## Subscripts

## Operators

## Variables

mopack provides several variables that you can use in your configuration files
in order to programmatically define how to resolve or use your dependencies.

`cfgdir` <span class="subtitle">*availability*: everywhere</span>
: The directory containing the current mopack configuration file.

`srcdir` <span class="subtitle">*availability*: [source distributions](packages.md#source-distributions)</span>
: The directory containing the source code for the current package.

`builddir` <span class="subtitle">*availability*: [builders](builders.md), [usage](usage.md)</span>
: The directory to put the compiled output from a source distribution.

`deploy_dirs` <span class="subtitle">*availability*: everywhere</span>
: A dictionary of directories specifying where to deploy package data to. These
  can be specified in the [`options`](file-structure.md#options) section.

`host_platform` <span class="subtitle">*availability*: everywhere</span>
: The name of the current platform (the one being used to build your project).
  Possible values include `linux`, `windows`, or `darwin`.

`target_platform` <span class="subtitle">*availability*: everywhere</span>
: The name of the platform that binaries are being built for.

`env` <span class="subtitle">*availability*: everywhere</span>
: A dictionary of environment variables. These can be set by the calling
  environment or overridden in the [`options`](file-structure.md#options)
  section.

`submodule` <span class="subtitle">*availability*: [submodule maps](usage.md)</span>
: The name of the user-specified submodule. You can use this to automatically
  generate submodule configuration for the `*` placeholder submodule.

