# Changes

## v0.2.0
in progress
{: .subtitle}

### New features
- `build` field for source distributions can now take a list of builders
- Source distribution packages and builders now accept an `env` field
- New builders `b2` and `ninja`
- Verbose output of build commands now prints iteratively
- New expression variable `symbols`, a dictionary of all defined symbols

### Breaking changes
- Source distribution configurations no longer inherit defaults automatically;
  set `inherit_defaults` to `true` if you want this
- `usage`/`usages` are now `linkage`/`linkages`
- `custom` builders that use the `build/` output directory should set
  `outdir: build`
- Linkages now use `submodule_linkage` instead of `submodule_map`
- `auto_link` field for `path`/`system` linkage is now obsolete; instead, you
  can use the expression variable `auto_link` to define different linkage when
  auto-linking is available

---

## v0.1.0
2023-05-15
{: .subtitle}

- Initial release
