API Reference
=============

.. automodule:: referencing
   :members:
   :undoc-members:
   :imported-members:
   :special-members: __iter__, __getitem__, __len__, __rmatmul__


Private Objects
---------------

The following objects are private in the sense that constructing or importing them is not part of the `referencing` public API, as their name indicates (by virtue of beginning with an underscore).

They are however public in the sense that other public API functions may return objects of these types.

Plainly then, you may rely on their methods and attributes not changing in backwards incompatible ways once `referencing` itself is stable, but may not rely on importing or constructing them yourself.

.. autoclass:: referencing._core.Resolved
   :members:
   :undoc-members:


.. autoclass:: referencing._core.Retrieved
   :members:
   :undoc-members:


.. autoclass:: referencing._core.AnchorOrResource


.. autoclass:: referencing._core.Resolver
   :members:
   :undoc-members:


.. autoclass:: referencing._core._MaybeInSubresource
   :members:
   :undoc-members:

.. class:: referencing._core._Unset

   A sentinel object used internally to satisfy the type checker.

   Neither accessing nor explicitly passing this object anywhere is public API, and it is only documented here at all to get Sphinx to not complain.


Submodules
----------

referencing.jsonschema
^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: referencing.jsonschema
   :members:
   :undoc-members:


referencing.exceptions
^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: referencing.exceptions
   :members:
   :show-inheritance:
   :undoc-members:


referencing.retrieval
^^^^^^^^^^^^^^^^^^^^^

.. automodule:: referencing.retrieval
   :members:
   :undoc-members:


.. autoclass:: referencing.retrieval._T


referencing.typing
^^^^^^^^^^^^^^^^^^

.. automodule:: referencing.typing
   :members:
   :undoc-members:
