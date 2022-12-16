# Expressions

Sometimes, how a dependency should be resolved depends on the system you're
using. For example, you would only use [apt](packages.md#apt) dependencies on
Linux systems. To support this, mopack lets you write your dependency
configurations using expressions.

## Introducing expressions

You can introduce expressions with `${ ... }`, or `$` if the expression is just
a variable name. When defining the expression for [conditional package
definitions](file-structure.md#conditional-package-definitions), this introducer
isn't necessary (a conditional is always an expression to begin with).

## Literals

<!-- boolean, null, integer, string, array -->

## Variables

## Subscripts

## Operators
