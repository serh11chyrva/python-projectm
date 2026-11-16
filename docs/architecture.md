# Architecture and resource lifetime

## Package layers

| Layer | Responsibility |
| --- | --- |
| `pypm_wrapper/` | C ABI over projectM, native errors, framebuffer targeting, and string ownership |
| `python_projectm/native/` | Lazy library discovery, ctypes signatures, and native exceptions |
| `python_projectm/core/` | ProjectM lifetime, validated PCM, presets, parameters, and version queries |
| `python_projectm/gl/` | Context identity, thread guards, GL state preservation, and framebuffer resources |
| `python_projectm/integrations/` | GLFW, ModernGL, NumPy, and PySide6 adapters |

The Python package and adapters defer native loading until a native function is
called. Importing a module does not initialize GLFW, create a Qt application,
allocate an OpenGL context, or load `pypm_capi`. Optional adapter modules still
require their Python toolkit packages during normal application use.

## One instance, one native context, one thread

Create a core instance while a desktop OpenGL 3.3+ context is current. Its
guard records the thread and the native context identity. Rendering, preset
loading, audio submission, parameter access, and cleanup use that same pair.
Shared textures do not make different contexts interchangeable; framebuffer
and vertex-array objects remain context-specific.

Managed renderers activate an adapter around each operation. Their `current()`
scope exposes the full core API for parameter changes. A renderer's outer
`with` statement controls lifetime without keeping its context current between
calls. GLFW and Qt adapters restore the preceding context from their own
toolkit; avoid nesting unrelated toolkit providers.

## Cleanup order

1. Stop timers and producers that submit rendering or PCM work.
2. Stop and join any rendering worker using its documented GUI-thread shutdown.
3. Close renderers, projectM instances, textures, and FBOs in their original
   current context and thread.
4. Destroy owned contexts and surfaces.
5. Terminate global GLFW state or destroy the Qt application when the application
   owns that lifetime.

Adapters leave borrowed contexts and windows alive. `close()` is idempotent,
but a destructor cannot recover a context that has already disappeared. Explicit
cleanup is required for reliable resource release.

## Rendering and state

The core renders to the current draw framebuffer or an explicit FBO ID.
Managed GLFW rendering selects the window framebuffer. The Qt widget renders
to `defaultFramebufferObject()` using physical pixel dimensions. ModernGL and
NumPy adapters own texture-backed output targets.

Rendering normally preserves the GL state used by projectM. Setting
`preserve_state=False` lets an application manage that state itself and requires
rebinding whatever subsequent drawing needs. NumPy readback returns writable
RGBA8 arrays and optionally flips OpenGL's bottom-left origin to top-left.

## Native framebuffer adaptation

Upstream projectM 4.1.6 binds framebuffer zero for final composition. The root
CMake build uses `cmake/ProjectMFramebuffer.cmake` to verify expected source
fragments and compile a generated copy of `ProjectM.cpp` from the build
directory. That copy retains the caller's target framebuffer.

The adaptation preserves upstream source files and interfaces. The wrapper
and the adapted projectM library must be built and deployed together; an
unrelated prebuilt projectM binary cannot provide the same framebuffer behavior.
Follow the [installation guide](installation.md) for the supported procedure.
