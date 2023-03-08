=======================================
Introduction to the ``referencing`` API
=======================================

When authoring JSON documents, it is often useful to be able to reference other JSON documents, or to reference subsections of other JSON documents.

This kind of JSON referencing has historically been defined by various specifications, with slightly differing behavior.
The JSON Schema specifications, for instance, define :kw:`$ref` and :kw:`$dynamicRef` keywords to allow schema authors to combine multiple schemas together for reuse or deduplication as part of authoring JSON schemas.

The `referencing <index>` library was written in order to provide a simple, well-behaved and well-tested implementation of JSON reference resolution in a way which can be used across multiple specifications or specification versions.


Core Concepts
-------------

There are 3 main objects to be aware of:

    * `referencing.Registry`, which represents a specific immutable set of resources (either in-memory or retrievable)
    * `referencing.Specification`, which represents a specific specification, such as JSON Schema Draft 7, which can have differing referencing behavior from other specifications or even versions of JSON Schema.
      JSON Schema-specific specifications live in the `referencing.jsonschema` module and are named like `referencing.jsonschema.DRAFT202012`.
    * `referencing.Resource`, which represents a specific resource (often a Python `dict`) *along* with a specific `referencing.Specification` it is to be interpreted under.

As a concrete example, the simple JSON Schema ``{"type": "integer"}`` may be interpreted as a schema under either Draft 2020-12 or Draft 4 of the JSON Schema specification (amongst others); in draft 2020-12, the float ``2.0`` must be considered an integer, whereas in draft 4, it potentially is not.
If you mean the former (i.e. to associate this schema with draft 2020-12), you'd use ``referencing.Resource(contents={"type": "integer"}, specification=referencing.jsonschema.DRAFT202012)``, whereas for the latter you'd use `referencing.jsonschema.DRAFT4`.

A resource may be identified via one or more URIs, either because they identify themselves in a way proscribed by their specification (e.g. an :kw:`$id` keyword in suitable versions of the JSON Schema specification), or simply because you wish to externally associate a URI with the resource, regardless of a specification-specific way to refer to itself.
You could add the aforementioned simple JSON Schema resource to a `referencing.Registry` by creating an empty registry and then identifying it via some URI:

.. testcode::

    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    resource = Resource(contents={"type": "integer"}, specification=DRAFT202012)
    registry = Registry().with_resource(uri="http://example.com/my/resource", resource=resource)
    print(registry)

.. testoutput::

   <Registry (1 uncrawled resource)>

.. note::

    `referencing.Registry` is an entirely immutable object.
    All of its methods which add resources to itself return *new* registry objects containing the added resource.

You could also confirm your resource is in the registry if you'd like, via `referencing.Registry.contents`, which will show you the contents of a resource at a given URI:

.. testcode::

   print(registry.contents("http://example.com/my/resource"))

.. testoutput::

   {'type': 'integer'}
