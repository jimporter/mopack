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

<!-- boolean, null, integer, string, array -->

## Variables

`cfgdir` <span class="subtitle">*availability*: everywhere</span>
: FIXME

`srcdir` <span class="subtitle">*availability*: FIXME</span>
: FIXME

`builddir` <span class="subtitle">*availability*: [builders](builders.md)</span>
: FIXME

`deploy_dirs` <span class="subtitle">*availability*: everywhere</span>
: FIXME

`host_platform` <span class="subtitle">*availability*: everywhere</span>
: FIXME

`target_platform` <span class="subtitle">*availability*: everywhere</span>
: FIXME

`env` <span class="subtitle">*availability*: everywhere</span>
: FIXME

`submodule` <span class="subtitle">*availability*: FIXME</span>
: FIXME

## Subscripts

## Operators
