API reference
=============

The reference is generated from the Python source docstrings. Importing modules
for documentation does not create a projectM instance or load native libraries.

Start with :class:`python_projectm.ProjectM` when your application already has a
current desktop OpenGL context. Managed renderers activate a supplied context
around each operation and expose the core through their ``current()`` scope.

.. toctree::
   :maxdepth: 2

   core
   rendering
   integrations
   native
