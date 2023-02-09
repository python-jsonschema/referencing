==================
External Retrieval
==================

`Registry` objects represent collections of in-memory resources (e.g. in the case of JSON Schema registries, they represent collections of in-memory JSON Schemas).

Occasionally one wishes to dynamically fetch resources from some other location.
We'll refer to resources not present in-memory as "external resources"

The JSON Schema specifications generally discourage implementations from automatically retrieving network resources [#]_, but if you are in a situation where you wish to do so, or if you wish alternatively to load resources from a database, or from the filesystem, you can do so via the ``retrieve`` argument to `Registry` objects.

Here's an example of how to automatically retrieve external references by downloading them from their URI via :httpx:`httpx </>`, shown by automatically retrieving one of the JSON Schema metaschemas from the network:

.. code:: python

    from referencing import Registry, Resource
    import httpx


    def retrieve_via_httpx(uri):
        response = httpx.get(uri)
        return Resource.from_contents(response.json())


    registry = Registry(retrieve=retrieve_via_httpx)
    resolver = registry.resolver()
    print(resolver.lookup("https://json-schema.org/draft/2020-12/schema"))

.. [#] Often for good security reasons. See :kw:`schema-references`.
