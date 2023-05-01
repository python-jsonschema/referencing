An implementation-agnostic implementation of JSON reference resolution.

In other words, a way for e.g. JSON Schema tooling to resolve the ``$ref`` keyword across all drafts without needing to implement support themselves.

This library is meant for use both by implementers of JSON referencing-related tooling -- like JSON Schema implementations supporting the :kw:`$ref` keyword -- as well as by end-users using said implementations who wish to then configure sets of resources (like schemas) for use at runtime.

The simplest example of populating a registry (typically done by end-users) and then looking up a resource from it (typically done by something like a JSON Schema implementation) is:

.. testcode::

    from referencing import Registry, Resource
    import referencing.jsonschema

    schema = Resource.from_contents(  # Parse some contents into a 2020-12 JSON Schema
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:example:a-202012-schema",
            "$defs": {
                "nonNegativeInteger": {
                    "$anchor": "nonNegativeInteger",
                    "type": "integer",
                    "minimum": 0,
                },
            },
        }
    )
    registry = schema @ Registry()  # Add the resource to a new registry

    # From here forward, this would usually be done within a library wrapping this one,
    # like a JSON Schema implementation
    resolver = registry.resolver()
    resolved = resolver.lookup("urn:example:a-202012-schema#nonNegativeInteger")
    assert resolved.contents == {
        "$anchor": "nonNegativeInteger",
        "type": "integer",
        "minimum": 0,
    }

For fuller details, see the `intro`.


.. toctree::
    :glob:
    :hidden:

    intro
    schema-packages
    compatibility
    api
    changes
