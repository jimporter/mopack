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
    linkage:
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
      origin: apt
      # ...
    - origin: tarball
      # ...
```

## Literals

Within expressions, you can use a variety of literal types:

* booleans (`true` or `false`)
* null values (`null`)
* integers (decimal digits, possibly preceded by `-`)
* strings (quoted using either `'` or `"`, and with `\` for escapes)
* arrays (`[value, ...]`)

## Operators

As you might expect, you can use operators within your expressions to manipulate
values. The table below lists all the supported operators, with the precedence
and associativity:

| Precedence | Operator    | Meaning                  | Associativity |
|------------|-------------|--------------------------|---------------|
| 1          | `x[y]`      | Subscript                | Left          |
| 2          | `!x`        | Logical not              | Right         |
|            | `-x`        | Arithmetic negation      | Right         |
| 3          | `x * y`     | Multiplication           | Left          |
|            | `x / y`     | Division                 | Left          |
|            | `x % y`     | Modulo                   | Left          |
| 4          | `x + y`     | Addition/concatenation   | Left          |
|            | `x - y`     | Subtraction              | Left          |
| 5          | `x > y`     | Greater than             | Left          |
|            | `x >= y`    | Greater than or equal to | Left          |
|            | `x < y`     | Less than                | Left          |
|            | `x <= y`    | Less than or equal to    | Left          |
| 6          | `x == y`    | Equal to                 | Left          |
|            | `x != y`    | Not equal to             | Left          |
| 7          | `x && y`    | Logical and              | Left          |
|            | `x || y`    | Logical or               | Left          |
| 8          | `x ? y : z` | Ternary conditional      | Right         |

## Variables

mopack provides several variables that you can use within expressions in order
to programmatically define how to resolve or use your dependencies.

`symbols` <span class="subtitle">*availability*: everywhere</span>
: A special dictionary variable whose key-value pairs are every defined
  variable. You can use this to refer to variables which may not be defined in
  certain contexts, such as `srcdir`.

`cfgdir` <span class="subtitle">*availability*: everywhere</span>
: The directory containing the current mopack configuration file.

`srcdir` <span class="subtitle">*availability*: [source distributions](packages.md#source-distributions)</span>
: The directory containing the source code for the current package.

`builddir` <span class="subtitle">*availability*: [builders](builders.md), [linkage](linkage.md)</span>
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

`auto_link` <span class="subtitle">*availability*: everywhere</span>
: True if the compiler in use supports auto-linking (e.g.
  [MSVC][msvc-auto-link]).

`submodule` <span class="subtitle">*availability*: [submodule maps](linkage.md)</span>
: The name of the user-specified submodule. You can use this to automatically
  generate submodule configuration for the `*` placeholder submodule.

[msvc-auto-link]: https://learn.microsoft.com/en-us/cpp/preprocessor/comment-c-cpp?view=msvc-170#lib
