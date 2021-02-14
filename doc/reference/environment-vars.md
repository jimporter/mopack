# Environment Variables

mopack reads from a number of environment variables. Below is a full list of all
the environment variables mopack recognizes.

## Command variables
---

### *ADD_APT_REPOSITORY*
Default: `sudo add-apt-repository`
{: .subtitle}

The command to use when adding an apt repository.

### *APT_GET*
Default: `sudo apt-get`
{: .subtitle}

The command to use when installing an apt package.

### *BFG9000*
Default: `bfg9000`
{: .subtitle}

The command to use when configuring a [bfg9000][bfg9000]-based project.

### *CONAN*
Default: `conan`
{: .subtitle}

The command to use when installing a [conan][conan] package.

### *CMAKE*
Default: `cmake`
{: .subtitle}

The command to use when configuring a [CMake][cmake]-based project.

### *GIT*
Default: `git`
{: .subtitle}

The command to use when working with a [git][git] repository.

### *NINJA*
Default: `ninja`
{: .subtitle}

The command to use when building via the [Ninja][ninja] build system.

### *PATCH*
Default: `patch`
{: .subtitle}

The command to use when applying a patch file.

## System variables
---

### *CLICOLOR*
Default: *none*
{: .subtitle}

If set to `0`, disable colors in terminal output, overriding the `--color`
option and tty detection. If set to non-zero, enable colors if outputting to a
tty.

### *CLICOLOR_FORCE*
Default: *none*
{: .subtitle}

If set to non-zero, enable colors in the terminal output regardless of whether
the destination is a tty. This overrides [*CLICOLOR*](#CLICOLOR).

[bfg9000]: https://jimporter.github.io/bfg9000/
[conan]: https://conan.io/
[cmake]: https://cmake.org/
[git]: https://git-scm.com/
[ninja]: https://ninja-build.org/
