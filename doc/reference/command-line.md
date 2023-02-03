# Command-Line Reference

## Global options

#### `-h`, `--help` { #help-option }

Print a help message and exit. Equivalent to the [`help`](#help) subcommand.

#### `--verbose` { #verbose }

Show verbose output, e.g. the output of build commands during `mopack resolve`.

#### `-c`, <code>--color *WHEN*</code> { #color }

Show colored output; *WHEN* is one of `always`, `never`, or `auto` and defaults
to `auto` (i.e. show colored output when the terminal is a tty). `-c` is
equivalent to `--color=always`.

#### `--warn-once` { #warn-once }

Only emit a given warning once.

## Sub-commands

### <code>mopack help [*SUBCOMMAND*]</code> { #help }

Print a help message and exit. If *SUBCOMMAND* is specified, print help for that
subcommand.

### <code>mopack resolve [*FILE*]</code> { #resolve }

Fetch dependencies from their origins and prepare them for use by the current
project (e.g. by building them).

#### <code>--directory *PATH*</code> { #resolve-directory }

The directory storing the local package data; defaults to `./mopack`.

#### <code>-P *TYPE*=*PATH*</code>, <code>--deploy-path *TYPE*=*PATH*</code> { #resolve-deploy-path }

Set the directory to deploy package data type *TYPE* to *PATH*. *TYPE* is a
GNU-like [directory variable][gnu-directory-variables], such as `prefix` or
`bindir`.

#### <code>-o *OPTION*=*VALUE*</code>, <code>--option *OPTION*=*VALUE*</code> { #resolve-option }

Override the common option *OPTION* to be *VALUE*.

#### <code>-S *OPTION*=*VALUE*</code>, <code>--origin-option *OPTION*=*VALUE*</code> { #resolve-origin-option }

Override the origin option *OPTION* to be *VALUE*.

#### <code>-B *OPTION*=*VALUE*</code>, <code>--builder-option *OPTION*=*VALUE*</code> { #resolve-builder-option }

Override the builder option *OPTION* to be *VALUE*.

#### `--strict` { #resolve-strict }

Return an error during [`mopack usage`](#usage) if the requested dependency is
not defined.

### <code>mopack usage [*DEPENDENCY*]</code> { #usage }

Retrieve information about how to use a dependency. This returns
[metadata](usage.md#usage-results) in YAML format (or JSON if `--json` is
passed) pointing to a pkg-config .pc file.

#### <code>--directory *PATH*</code> { #usage-directory }

The directory storing the local package data; defaults to `./mopack`.

#### `--json` { #usage-json }

Display usage results as JSON.

#### `--strict` { #usage-strict }

Return an error if the requested dependency is not defined.

### <code>mopack deploy</code> { #deploy }

Copy the project's dependencies to an installation directory (e.g. as part of
running a command like `make install`).

#### <code>--directory *PATH*</code> { #deploy-directory }

The directory storing the local package data; defaults to `./mopack`.

### <code>mopack clean</code> { #clean }

Clean the `mopack` package directory of all files.

#### <code>--directory *PATH*</code> { #clean-directory }

The directory storing the local package data; defaults to `./mopack`.

### <code>mopack list-files</code> { #list-files }

List all the input files used by the current configuration.

#### <code>--directory *PATH*</code> { #list-files-directory }

The directory storing the local package data; defaults to `./mopack`.

#### `--I`, `--include-implicit` { #list-files-include-implicit }

Include implicit input files.

#### `--json` { #list-files-json }

Display results as JSON.

#### `--strict` { #usage-strict }

Return an error if the package directory does not exist.

### <code>mopack list-packages</code>, <code>mopack ls</code> { #list-packages }

List all the package dependencies.

#### <code>--directory *PATH*</code> { #list-packages-directory }

The directory storing the local package data; defaults to `./mopack`.

#### `--flat` { #list-packages-flat }

List packages without hierarchy.

### `mopack generate-completion` { #generate-completion }

Generate shell-completion functions for mopack and write them to standard
output. This requires the Python package [shtab][shtab].

#### <code>-s *SHELL*</code>, <code>--shell *SHELL*</code> { #generate-completion-shell }

Specify the shell to generate completion for, e.g. `bash`. Defaults to the
current shell's name.

[gnu-directory-variables]: https://www.gnu.org/prep/standards/html_node/Directory-Variables.html
[shtab]: https://github.com/iterative/shtab
