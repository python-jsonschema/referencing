============
Introduction
============

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


Populating Registries
---------------------

There are a few different methods you can use to populate registries with resources.
Which one you want to use depends on things like:

    * do you already have an instance of `referencing.Resource`, or are you creating one out of some loaded JSON?
      If not, does the JSON have some sort of identifier that can be used to determine which specification it belongs to (e.g. the JSON Schema ``$schema`` keyword)?
    * does your resource have an internal ID (e.g. the JSON Schema ``$id`` keyword)?
    * do you have additional (external) URIs you want to refer to the same resource as well?
    * do you have one resource to add or many?

We'll assume for example's sake that we're dealing with JSON Schema resources for the following examples, and we'll furthermore assume you have some initial `referencing.Registry` to add them to, perhaps an empty one:

.. testcode::

    from referencing import Registry
    initial_registry = Registry()

Recall that registries are immutable, so we'll be "adding" our resources by creating new registries containing the additional resource(s) we add.

In the ideal case, you have a JSON Schema with an internal ID, and which also identifies itself for a specific version of JSON Schema e.g.:

.. code:: json

    {
      "$id": "urn:example:my-schema",
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "type": "integer"
    }

If you have such a schema in some JSON text, and wish to add a resource to our registry and be able to identify it using its internal ID (``urn:example:my-schema``) you can simply use:

.. testcode::

    import json

    loaded = json.loads(
        """
        {
          "$id": "urn:example:my-schema",
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "integer"
        }
        """,
    )
    resource = Resource.from_contents(loaded)
    registry = resource @ initial_registry

which will give you a registry with our resource added to it.
Let's check by using `Registry.contents`, which takes a URI and should show us the contents of our resource:

.. testcode::

    print(registry.contents("urn:example:my-schema"))

.. testoutput::

    {'$id': 'urn:example:my-schema', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'integer'}

If your schema did *not* have a ``$schema`` keyword, you'd get an error:

.. testcode::

    another = json.loads(
        """
        {
          "$id": "urn:example:my-second-schema",
          "type": "integer"
        }
        """,
    )
    print(Resource.from_contents(another))

.. testoutput::

    Traceback (most recent call last):
        ...
    referencing.exceptions.CannotDetermineSpecification: {'$id': 'urn:example:my-second-schema', 'type': 'integer'}

which is telling you that the resource you've tried to create is ambiguous -- there's no way to know which version of JSON Schema you intend it to be written for.

You can of course instead directly create a `Resource`, instead of using `Resource.from_contents`, which will allow you to specify which version of JSON Schema you're intending your schema to be written for:

.. testcode::

    import referencing.jsonschema
    second = Resource(contents=another, specification=referencing.jsonschema.DRAFT202012)

and now of course can add it as above:

.. testcode::

    registry = second @ registry
    print(registry.contents("urn:example:my-second-schema"))

.. testoutput::

    {'$id': 'urn:example:my-second-schema', 'type': 'integer'}

As a shorthand, you can also use `Specification.create_resource` to create a `Resource` slightly more tersely.
E.g., an equivalent way to create the above resource is:

.. testcode::

    second_again = referencing.jsonschema.DRAFT202012.create_resource(another)
    print(second_again == second)

.. testoutput::

    True

If your resource doesn't contain an ``$id`` keyword, you'll get a different error if you attempt to add it to a registry:

.. testcode::

    third = Resource(
        contents=json.loads("""{"type": "integer"}"""),
        specification=referencing.jsonschema.DRAFT202012,
    )
    registry = third @ registry

.. testoutput::

    Traceback (most recent call last):
        ...
    referencing.exceptions.NoInternalID: Resource(contents={'type': 'integer'}, _specification=<Specification name='draft2020-12'>)

which is now saying that there's no way to add this resource to a registry directly, as it has no ``$id`` -- you must provide whatever URI you intend to use to refer to this resource to be able to add it.

You can do so using `referencing.Registry.with_resource` instead of the `@ operator <referencing.Registry.__rmatmul__>` which we have used thus far, and which takes the explicit URI you wish to use as an argument:

.. testcode::

    registry = registry.with_resource(uri="urn:example:my-third-schema", resource=third)

which now allows us to use the URI we associated with our third resource to retrieve it:

.. testcode::

    print(registry.contents("urn:example:my-third-schema"))

.. testoutput::

    {'type': 'integer'}

If you have more than one resource to add, you can use `Registry.with_resources` (with an ``s``) to add many at once, or, if they meet the criteria to use ``@``, you can use ``[one, two, three] @ registry`` to add all three resources at once.

You may also want to have a look at `Registry.with_contents` for a further method to add resources to a registry without constructing a `Resource` object yourself.


Dynamically Retrieving Resources
--------------------------------

Sometimes one wishes to dynamically retrieve or construct `Resource`\ s which *don't* already live in-memory within a `Registry`.
This might be resources retrieved dynamically from a database, from files somewhere on disk, from some arbitrary place over the internet, or from the like.
We'll refer to such resources not present in-memory as *external resources*.

The ``retrieve`` argument to ``Registry`` objects can be used to configure a callable which will be used anytime a requested URI is *not* present in the registry, thereby allowing you to retrieve it from whichever location it lives in.
Here's an example of automatically retrieving external references by downloading them via :httpx:`httpx </>`, illustrated by then automatically retrieving one of the JSON Schema metaschemas from the network:

.. code:: python

    from referencing import Registry, Resource
    import httpx


    def retrieve_via_httpx(uri):
        response = httpx.get(uri)
        return Resource.from_contents(response.json())


    registry = Registry(retrieve=retrieve_via_httpx)
    resolver = registry.resolver()
    print(resolver.lookup("https://json-schema.org/draft/2020-12/schema"))

.. note::

    In the case of JSON Schema, the specifications generally discourage implementations from automatically retrieving these sorts of external resources over the network due to potential security implications.
    See :kw:`schema-references` in particular.

    `referencing` will of course therefore not do any such thing automatically, and this section generally assumes that you have personally considered the security implications for your own use case.
