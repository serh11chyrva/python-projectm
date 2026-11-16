Native loading and errors
=========================

Applications should normally use :class:`python_projectm.ProjectM` or a managed
renderer. The ``native`` package is the low-level ctypes layer used by the core.
Raw C calls do not provide the Python core's context, thread, or input guards.

Library discovery
-----------------

The loader looks for ``pypm_capi.dll`` on Windows, ``libpypm_capi.dylib`` on macOS,
or ``libpypm_capi.so`` on other platforms in ``python_projectm/native/bin/``.
The documented native build and deployment procedure covers Windows x64.

Set ``PYTHON_PROJECTM_LIBRARY`` to a full wrapper path before the first native
call to select an application-managed deployment. Place matching projectM runtime
libraries beside it. The loader caches its result for the process; changing the
environment variable later does not replace the loaded library.

.. autofunction:: python_projectm.native.loader.load_native_library

.. autofunction:: python_projectm.native.loader.load_glew_library

Exceptions
----------

The loader raises native errors directly. Core operations translate native call
errors to :class:`python_projectm.ProjectMError`.

.. autoexception:: python_projectm.native.errors.NativeError

.. autoexception:: python_projectm.native.errors.NativeLibraryNotFound

.. autoexception:: python_projectm.native.errors.NativeSymbolError

ABI and memory ownership
------------------------

``pypm_wrapper/include/pypm_capi.h`` declares the C ABI, implemented by
``pypm_wrapper/src/pypm_capi.cpp`` and mirrored by
``python_projectm/native/bindings.py``. Changes must keep all three consistent.

* ``pypm_create`` returns an opaque instance handle. Destroy it exactly once
  through ``pypm_destroy`` while the original thread and GL context are available.
* The last-error string is borrowed thread-local storage, valid until the next
  wrapper call. Do not free it.
* The two C version functions return allocated strings. The bindings copy each
  string and call ``pypm_free_string`` with projectM's allocator.
* PCM counts are frames per channel, rather than the number of scalar values.
  The core copies incompatible array storage and splits large submissions.

The API reference reads Python docstrings; it does not compile or execute this
native interface. See :doc:`/architecture` for the framebuffer adaptation and
:doc:`/installation` for the native build procedure.
