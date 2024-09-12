# Changes

## v0.2.0 (in progress)

### New features
- `build` field for source distributions can now take a list of builders
- Source distribution packages and builders now accept an `env` field
- New builders `b2` and `ninja`
- Verbose output of build commands now prints iteratively
- New expression variable `symbols`, a dictionary of all defined symbols

### Breaking changes
- `usage`/`usages` are now `linkage`/`linkages`
- `custom` builders that use the `build/` output directory should set
  `outdir: build`

---

## v0.1.0 (2023-05-15)

- Initial release
