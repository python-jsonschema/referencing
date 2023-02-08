===============
Schema Packages
===============

The `Registry` object is a useful way to ship Python packages which essentially bundle a set of JSON Schemas for use at runtime from Python.

In order to do so, you likely will want to:

* Collect together the JSON files you wish to ship
* Put them inside a Python package (one you possibly tag with the ``jsonschema`` keyword for easy discoverability).
  Remember to ensure you have configured your build tool to include the JSON files in your built package distribution -- for e.g. :hatch:`hatch </>` this is likely automatic, but for `setuptools <setuptools:index>` may involve creating a suitable :file:`MANIFEST.in`.
* Instantiate a `Registry` object somewhere globally within the package
* Call `Registry.crawl` at import-time, such that users of your package get a "fully ready" registry to use

For an example of such a package, see `jsonschema-specifications <jsonschema-specifications:index>`, which bundles the JSON Schema "official" schemas for use.
