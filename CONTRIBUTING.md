# Contributing

See the [source build guide](https://python-projectm.readthedocs.io/en/latest/source-build.html)
for the native toolchain and editable installation. The bindings and wrapper
share a stable C interface; changes must keep the header, implementation, and
ctypes declarations consistent. Keep OpenGL operations and cleanup on the
thread owning the current context.

Write documentation, identifiers, messages, and commits in English. Keep changes
focused and preserve other working-tree changes. Follow `AGENTS.md` when using
an automated coding agent; local checks require an explicit request.

## Dependencies

Runtime dependencies and extras are declared in `pyproject.toml` and locked in
`uv.lock`. After an authorized runtime dependency update:

```console
uv lock
uv export --frozen --all-extras --no-emit-project --format requirements.txt --output-file requirements.txt
```

Commit the declarations, lockfile, and regenerated requirements together.
Build-tool pins live in the build-system table. CI harness requirements and
documentation requirements are maintained separately from application dependencies.
Native source checksums and the vcpkg baseline live in `native-sources.json`;
keep the vcpkg manifest baseline consistent when changing native inputs.

## Checks and releases

The existing [unittest suites](tests/README.md) cover unit behavior and opt-in
real rendering. [Documentation instructions](docs/documentation.md) describe the
strict Sphinx build. CI runs both, builds the Windows x64 wheel, and tests its
installation outside the checkout. No new test framework is required.

Use Conventional Commits, such as `fix(native): retain DLL search directories`.
See the [release guide](docs/publishing.md) for publishing setup, versioning,
corresponding-source distribution, and release validation.
