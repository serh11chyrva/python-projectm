Core API
========

.. currentmodule:: python_projectm

ProjectM
--------

The main entry point combines rendering, presets, settings, and PCM submission.
All core calls require the original context to be current on the creating thread.

.. autoclass:: ProjectM
   :members:
   :inherited-members:

Lifecycle and rendering base
----------------------------

.. autoclass:: ProjectMCore
   :members:

Mixins
------

These classes remain available for existing imports. Applications normally use
the combined :class:`ProjectM` API rather than constructing mixins themselves.

.. currentmodule:: python_projectm.core.audio

.. autoclass:: AudioMixin
   :members:

.. currentmodule:: python_projectm.core.presets

.. autoclass:: PresetsMixin
   :members:

.. currentmodule:: python_projectm.core.parameters

.. autoclass:: ParametersMixin
   :members:

Version queries
---------------

These functions report the native projectM library version, independently of the
Python distribution's release number. Calling them loads the native wrapper but
does not need a current OpenGL context.

.. currentmodule:: python_projectm.core.version

.. autofunction:: get_version_string

.. autofunction:: get_vcs_version_string

Exceptions
----------

.. currentmodule:: python_projectm

.. autoexception:: ProjectMError

.. autoexception:: ProjectMNotInitialized

.. autoexception:: ProjectMContextError
