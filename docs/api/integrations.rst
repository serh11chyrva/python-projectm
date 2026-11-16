Rendering adapters
==================

See the :doc:`integration guide </integrations>` for working examples, PCM
formats, and shutdown rules. Renderer subclasses inherit preset, PCM, and
``current()`` methods from :class:`python_projectm.gl.Renderer`.

GLFW
----

.. currentmodule:: python_projectm.integrations.glfw

.. autoclass:: GLFWContext
   :members:

.. autoclass:: GLFWRenderer
   :members:
   :inherited-members:

ModernGL
--------

.. currentmodule:: python_projectm.integrations.moderngl

.. autoclass:: ModernGLContext
   :members:

.. autoclass:: ModernGLRenderer
   :members:
   :inherited-members:

NumPy
-----

.. currentmodule:: python_projectm.integrations.numpy

.. autoclass:: NumpyRenderer
   :members:
   :inherited-members:

PySide6
-------

.. currentmodule:: python_projectm.integrations.pyside6

Only project-specific widget methods are listed here; inherited Qt widget methods
follow the PySide6 API. The GUI event callbacks are invoked by Qt.

.. autoclass:: ProjectMWidget
   :members: fps, load_preset_file, load_preset, load_preset_data, add_pcm, current, cleanup

.. py:attribute:: ProjectMWidget.initialized

   No-argument Qt signal emitted after successful OpenGL initialization.

.. py:attribute:: ProjectMWidget.frame_rendered

   No-argument Qt signal emitted after each rendered frame.

.. py:attribute:: ProjectMWidget.error

   Qt signal carrying an exception from initialization, rendering, or a command.

.. autoclass:: QtGLContext
   :members:

.. autoclass:: QtOffscreenContext
   :members:
   :inherited-members:

.. autoclass:: NumpyViewport
   :members: set_frame

.. autoclass:: FrameEmitter

.. py:attribute:: FrameEmitter.frame_ready

   Qt signal carrying a new RGBA uint8 NumPy frame. Connect a GUI-thread slot
   such as :meth:`NumpyViewport.set_frame` to consume it.

.. py:attribute:: FrameEmitter.error

   Qt signal carrying the worker's most recently reported exception.

.. py:attribute:: FrameEmitter.finished

   No-argument Qt signal emitted after the worker releases its GL resources.

.. autoclass:: RenderThread
   :members: load_preset, load_preset_file, load_preset_data, add_pcm, resize, stop, join, close

.. autoclass:: GLFWProjectMCPURenderer

   Compatibility name for the GLFW-backed NumPy renderer. Prefer
   :class:`NumpyRenderer` or a Qt-native context for new code.
