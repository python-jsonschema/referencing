=============
Compatibility
=============

``referencing`` is currently in beta so long as version numbers begin with a ``0``, meaning its public interface may change if issues are uncovered, though not typically without reason.
Once it seems clear that the interfaces look correct (likely after ``referencing`` is in use for some period of time) versioning will move to `CalVer <https://calver.org/>`_ and interfaces will not change in backwards-incompatible ways without deprecation periods.

.. note::

    Backwards compatibility is always defined relative to the specifications we implement.
    Changing a behavior which is incorrect according to the relevant referencing specifications is not considered a backwards-incompatible change -- on the contrary, it's considered a bug fix.

In the spirit of `having some explicit detail on Bowtie's public interfaces <regret:before-you-deprecate:document your public api>`, here is a non-exhaustive list of things which are *not* part of the ``referencing`` public interface, and therefore which may change without warning, even once no longer in beta:

* All commonly understood indicators of privacy in Python -- in particular, (sub)packages, modules and identifiers beginning with a single underscore.
  In the case of modules or packages, this includes *all* of their contents recursively, regardless of their naming.
* All contents in the ``referencing.tests`` package unless explicitly indicated otherwise
* The precise contents and wording of exception messages raised by any callable, private *or* public.
* The precise contents of the ``__repr__`` of any type defined in the package.
* The ability to *instantiate* exceptions defined in `referencing.exceptions`, with the sole exception of those explicitly indicating they are publicly instantiable (notably `referencing.exceptions.NoSuchResource`).
* The instantiation of any type with no public identifier, even if instances of it are returned by other public API.
  E.g., `referencing._core.Resolver` is not publicly exposed, and it is not public API to instantiate it in ways other than by calling `referencing.Registry.resolver` or an equivalent.
  All of its public attributes are of course public, however.
* The concrete types within the signature of a callable whenever they differ from their documented types.
  In other words, if a function documents that it returns an argument of type ``Mapping[int, Sequence[str]]``, this is the promised return type, not whatever concrete type is returned which may be richer or have additional attributes and methods.
  Changes to the signature will continue to guarantee this return type (or a broader one) but indeed are free to change the concrete type.
* Any identifiers in any modules which are imported from other modules.
  In other words, if ``referencing.foo`` imports ``bar`` from ``referencing.quux``, it is *not* public API to use ``referencing.foo.bar``; only ``referencing.quux.bar`` is public API.
  This does not apply to any objects exposed directly on the ``referencing`` package (e.g. `referencing.Resource`), which are indeed public.
* Subclassing of any class defined throughout the package.
  Doing so is not supported for any object, and in general most types will raise exceptions to remind downstream users not to do so.

If any API usage may be questionable, feel free to open a discussion (or issue if appropriate) to clarify.
