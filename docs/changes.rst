=========
Changelog
=========

v0.25.0
-------

* Bump the minimum version of ``rpds.py`` used, enabling registries to be used from multiple threads.

v0.24.4
-------

* Fix handling of IDs with empty fragments (which are equivalent to URIs with no fragment)

v0.24.3
-------

* Further intro documentation

v0.24.2
-------

* Fix handling of ``additionalProperties`` with boolean value on Draft 4 (where the boolean isn't a schema, it's a special allowed value)

v0.24.1
-------

* Add a bit of intro documentation

v0.24.0
-------

* ``pyrsistent`` was replaced with ``rpds.py`` (Python bindings to the Rust rpds crate), which seems to be quite a bit faster.
  No user-facing changes really should be expected here.
