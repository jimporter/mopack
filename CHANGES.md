# Changes

## v0.2.0 (in progress)

### New features
- `build` field for source distributions can now take a list of builders
- New builder `ninja`
- Verbose output of build commands now prints iteratively

### Breaking changes
- `usage`/`usages` are now `linkage`/`linkages`
- `custom` builders that use the `build/` output directory should set
  `outdir: build`

---

## v0.1.0 (2023-05-15)

- Initial release
