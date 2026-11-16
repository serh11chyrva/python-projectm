# Agent Instructions

These instructions apply to the entire repository. Explicit authorization in the
current task is sufficient for the authorized action and scope; do not ask for the
same permission again.

## Language

- Write documentation, comments, docstrings, new code identifiers, program
  messages, commit messages, and pull request text in English.
- Respond in chat in the user's language unless they request another language.
- Do not translate existing content or rename existing APIs merely to enforce
  the language rule outside the requested task.

## Task Scope and Reporting

- Make only the changes needed for the requested task. Avoid unrelated fixes,
  cleanup, and refactoring; report other findings separately.
- Preserve existing user changes. Do not revert, overwrite, or include them in
  commits for your task.
- Update the relevant documentation when the task changes documented behavior.
- Keep the final report brief: describe the result, any checks actually
  performed, and material limitations.
- When checks were not requested, state that they were not run. There is no need
  to ask routinely whether to run them or to claim unverified behavior works.

## Checks and Test Files

- Without a separate explicit user request, limit verification to reading files,
  searching, and inspecting Git status and diffs.
- Do not run builds, CMake configuration, tests, linters, formatters, type
  checkers, applications, demos, or smoke checks without an explicit request.
  This includes import-based checks and other execution of project code.
- A normal implementation request does not authorize these checks. Do not replace
  a prohibited check with a smaller or indirect version of the same check.
- Create or modify test files only when explicitly requested. Permission to
  write tests does not imply permission to run them.
- When checks are requested, run only the requested scope. Do not install missing
  dependencies or broaden verification without authorization.

## Dependencies and Environment

- Obtain explicit authorization before adding or updating dependencies, changing
  their declared versions, installing packages, or introducing development tools.
- Obtain explicit authorization before creating or reconfiguring the development
  environment. A task that explicitly requests such a change already provides
  authorization for that scope.

## Git and Conventional Commits

- You may create local commits automatically after completing a task. A skipped
  check under the policy above does not itself prevent a local commit.
- Stage only your changes using explicit paths or selected hunks. Review the
  staged diff before committing. Leave any pre-existing staged user changes
  untouched and out of your commit.
- If your changes cannot be reliably separated from the user's changes, leave
  them uncommitted and explain why.
- Push changes or rewrite history only when explicitly requested.
- Before committing, inspect the configured Git hooks. If a hook would run checks
  that have not been authorized, defer the commit and report the reason. Do not
  bypass or disable hooks to make the commit.
- Use Conventional Commits: `type(scope): description`, with an optional scope.
  Use lowercase types from `feat`, `fix`, `docs`, `refactor`, `perf`, `test`,
  `build`, `ci`, `chore`, `style`, and `revert`.
- Write a concise English description in the imperative mood. Write any body and
  footers in English as well.
- For an authorized breaking change, add `!` before the colon and explain the
  incompatibility in a `BREAKING CHANGE:` footer. This notation does not replace
  the requirement to agree on the breaking change before editing.
- Example: `docs(agents): document agent workflow rules`.

## Project Architecture and Native Interfaces

- The C++ wrapper in `pypm_wrapper/` exposes the projectM C API to the `ctypes`
  bindings in `python_projectm/native/`. Higher-level APIs live in
  `python_projectm/core/`, with OpenGL helpers in `python_projectm/gl/` and optional
  integrations in `python_projectm/integrations/`. Keep changes in the appropriate
  layer.
- When changing a native interface, keep the C header, C++ implementation, and
  Python bindings consistent, including argument and return types, handle
  lifetimes, and memory ownership.
- For OpenGL operations, respect the active context, the thread on which it is
  current, and resource cleanup requirements. Do not assume a context is available
  on another thread.
- Preserve Python API and C ABI compatibility. Explain the consequences and
  obtain agreement before making incompatible changes.
- Do not modify third-party sources or generated artifacts unless necessary for
  the explicitly requested task. Never commit native binaries or build outputs.
- Refer to `README.md` for installation and build instructions rather than
  duplicating those commands here.
