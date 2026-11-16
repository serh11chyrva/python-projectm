OpenGL helpers
==============

.. currentmodule:: python_projectm.gl

Custom context adapters
-----------------------

A custom adapter implements the three methods in :class:`GLContext`. A restoring
``current()`` context manager is preferred when the toolkit supports one. It must
make the same native context current on the renderer's creating thread and restore
the preceding context on exit. Otherwise the renderer uses the
``make_current()`` / ``done_current()`` pair.

.. autoclass:: GLContext
   :members:

Managed renderer
----------------

.. autoclass:: Renderer
   :members:

Framebuffers
------------

``with FBO(...):`` temporarily binds a borrowed framebuffer. Entering an owned
``TextureFramebuffer`` also controls its binding, not its lifetime; call
``close()`` explicitly after leaving the binding scope and before destroying the
context.

.. autoclass:: FBO
   :members:

.. autoclass:: TextureFramebuffer
   :members:

State guards
------------

Use guards only while a valid context is current. They restore state but neither
create nor activate a context. Avoid rendering inside an active transform-feedback
operation or application query.

.. autoclass:: GLStateGuard
   :members:

.. autoclass:: ViewportGuard
   :members:
