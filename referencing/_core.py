from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import Any, Callable, ClassVar, Generic
from urllib.parse import unquote, urldefrag, urljoin

from attrs import evolve, field
from pyrsistent import m, plist, pmap, s
from pyrsistent.typing import PList, PMap, PSet

from referencing import exceptions
from referencing._attrs import frozen
from referencing.typing import URI, Anchor as AnchorType, D, Mapping


@frozen
class Specification(Generic[D]):
    """
    A specification which defines referencing behavior.

    The various methods of a `Specification` allow for varying referencing
    behavior across JSON Schema specification versions, etc.
    """

    #: A short human-readable name for the specification, used for debugging.
    name: str

    #: Find the ID of a given document.
    id_of: Callable[[D], URI | None]

    #: Retrieve the subresources of the given document (without traversing into
    #: the subresources themselves).
    subresources_of: Callable[[D], Iterable[D]]

    #: Retrieve the anchors contained in the given document.
    _anchors_in: Callable[
        [Specification[D], D],
        Iterable[AnchorType[D]],
    ] = field(alias="anchors_in")

    #: An opaque specification where resources have no subresources
    #: nor internal identifiers.
    OPAQUE: ClassVar[Specification[Any]]

    def __repr__(self):
        return f"<Specification name={self.name!r}>"

    def anchors_in(self, contents: D):
        """
        Retrieve the anchors contained in the given document.
        """
        return self._anchors_in(self, contents)

    def create_resource(self, contents: D) -> Resource[D]:
        """
        Create a resource which is interpreted using this specification.
        """
        return Resource(contents=contents, specification=self)


Specification.OPAQUE = Specification(
    name="opaque",
    id_of=lambda contents: None,
    subresources_of=lambda contents: [],
    anchors_in=lambda specification, contents: [],
)


@frozen
class Resource(Generic[D]):
    r"""
    A document (deserialized JSON) with a concrete interpretation under a spec.

    In other words, a Python object, along with an instance of `Specification`
    which describes how the document interacts with referencing -- both
    internally (how it refers to other `Resource`\ s) and externally (how it
    should be identified such that it is referenceable by other documents).
    """

    contents: D
    _specification: Specification[D] = field(alias="specification")

    @classmethod
    def from_contents(
        cls,
        contents: D,
        default_specification: Specification[D] = None,  # type: ignore[reportGeneralTypeIssues]  # noqa: E501
    ) -> Resource[D]:
        """
        Attempt to discern which specification applies to the given contents.

        Raises:

            `CannotDetermineSpecification`

                if the given contents don't have any discernible
                information which could be used to guess which
                specification they identify as
        """
        specification = default_specification
        if isinstance(contents, Mapping):
            jsonschema_dialect_id = contents.get("$schema")  # type: ignore[reportUnknownMemberType]  # noqa: E501
            if jsonschema_dialect_id is not None:
                from referencing.jsonschema import specification_with

                specification = specification_with(
                    jsonschema_dialect_id,  # type: ignore[reportUnknownArgumentType]  # noqa: E501
                    default=default_specification,
                )

        if specification is None:  # type: ignore[reportUnnecessaryComparison]
            raise exceptions.CannotDetermineSpecification(contents)
        return cls(contents=contents, specification=specification)  # type: ignore[reportUnknownArgumentType]  # noqa: E501

    @classmethod
    def opaque(cls, contents: D) -> Resource[D]:
        """
        Create an opaque `Resource` -- i.e. one with opaque specification.

        See `Specification.OPAQUE` for details.
        """
        return Specification.OPAQUE.create_resource(contents=contents)

    def id(self) -> URI | None:
        """
        Retrieve this resource's (specification-specific) identifier.
        """
        return self._specification.id_of(self.contents)

    def subresources(self) -> Iterable[Resource[D]]:
        """
        Retrieve this resource's subresources.
        """
        return (
            Resource.from_contents(
                each,
                default_specification=self._specification,
            )
            for each in self._specification.subresources_of(self.contents)
        )

    def anchors(self) -> Iterable[AnchorType[D]]:
        """
        Retrieve this resource's (specification-specific) identifier.
        """
        return self._specification.anchors_in(self.contents)

    def pointer(self, pointer: str, resolver: Resolver[D]) -> Resolved[D]:
        """
        Resolve the given JSON pointer.

        Raises:

            `exceptions.PointerToNowhere`

                if the pointer points to a location not present in the document
        """
        contents = self.contents
        for segment in unquote(pointer[1:]).split("/"):
            if isinstance(contents, Sequence):
                segment = int(segment)
            else:
                segment = segment.replace("~1", "/").replace("~0", "~")
            try:
                contents = contents[segment]  # type: ignore[reportUnknownArgumentType]  # noqa: E501
            except LookupError:
                raise exceptions.PointerToNowhere(ref=pointer, resource=self)

            # FIXME: this is slightly wrong, we need to know that we are
            #        entering a subresource specifically, not just any mapping
            if isinstance(contents, Mapping):
                subresource = self._specification.create_resource(contents)  # type: ignore[reportUnknownArgumentType]  # noqa: E501
                resolver = resolver.in_subresource(subresource)
        return Resolved(contents=contents, resolver=resolver)  # type: ignore[reportUnknownArgumentType]  # noqa: E501


def _fail_to_retrieve(uri: URI):
    raise exceptions.NoSuchResource(ref=uri)


@frozen
class Registry(Mapping[URI, Resource[D]]):
    r"""
    A registry of `Resource`\ s, each identified by their canonical URIs.

    Registries store a collection of in-memory resources, and optionally
    enable additional resources which may be stored elsewhere (e.g. in a
    database, a separate set of files, over the network, etc.).

    They also lazily walk their known resources, looking for subresources
    within them. In other words, subresources contained within any added
    resources will be retrievable via their own IDs (though this discovery of
    subresources will be delayed until necessary).

    Registries are immutable, and their methods return new instances of the
    registry with the additional resources added to them.

    The ``retrieve`` argument can be used to configure retrieval of resources
    dynamically, either over the network, from a database, or the like.
    Pass it a callable which will be called if any URI not present in the
    registry is accessed. It must either return a `Resource` or else raise an
    exception indicating that the resource is not retrievable.
    """

    _resources: PMap[URI, Resource[D]] = field(default=m(), converter=pmap)  # type: ignore[reportUnknownArgumentType]  # noqa: E501
    _anchors: PMap[tuple[URI, str], AnchorType[D]] = field(default=m())  # type: ignore[reportUnknownArgumentType]  # noqa: E501
    _uncrawled: PSet[URI] = field(default=s())  # type: ignore[reportUnknownArgumentType]  # noqa: E501
    _retrieve: Callable[[URI], Resource[D]] = field(default=_fail_to_retrieve)

    def __getitem__(self, uri: URI) -> Resource[D]:
        """
        Return the `Resource` identified by the given URI.
        """
        try:
            return self._resources[uri]
        except LookupError:
            try:
                return self._retrieve(uri)
            except exceptions.NoSuchResource:
                raise
            except Exception:
                raise exceptions.Unretrievable(ref=uri)

    def __iter__(self) -> Iterator[URI]:
        """
        Iterate over all known URIs in the registry.
        """
        return iter(self._resources)

    def __len__(self) -> int:
        """
        Count the total number of (fully crawled) resources in this registry.
        """
        return len(self._resources)

    def __repr__(self) -> str:
        size = len(self)
        pluralized = "resource" if size == 1 else "resources"
        if self._uncrawled:
            uncrawled = len(self._uncrawled)
            if uncrawled == size:
                summary = f"uncrawled {pluralized}"
            else:
                summary = f"{pluralized}, {uncrawled} uncrawled"
        else:
            summary = f"{pluralized}"
        return f"<Registry ({size} {summary})>"

    def remove(self, uri: URI):
        """
        Return a registry with the resource identified by a given URI removed.
        """
        if uri not in self._resources:
            raise exceptions.NoSuchResource(ref=uri)

        return evolve(
            self,
            resources=self._resources.remove(uri),
            uncrawled=self._uncrawled.discard(uri),
            anchors=pmap(
                (k, v) for k, v in self._anchors.items() if k[0] != uri
            ),
        )

    def anchor(self, uri: URI, name: str):
        """
        Retrieve the given anchor, which must already have been found.
        """
        return self._anchors[uri, name]

    def contents(self, uri: URI) -> D:
        """
        Retrieve the contents identified by the given URI.
        """
        return self._resources[uri].contents

    def crawl(self) -> Registry[D]:
        """
        Immediately crawl all added resources, discovering subresources.
        """
        resources = self._resources.evolver()
        anchors = self._anchors.evolver()
        uncrawled = [(uri, resources[uri]) for uri in self._uncrawled]
        while uncrawled:
            uri, resource = uncrawled.pop()

            id = resource.id()
            if id is not None:
                uri = urljoin(uri, id)
                resources[uri] = resource
            for each in resource.anchors():
                anchors.set((uri, each.name), each)
            uncrawled.extend((uri, each) for each in resource.subresources())
        return evolve(
            self,
            resources=resources.persistent(),
            anchors=anchors.persistent(),
            uncrawled=s(),
        )

    def with_resource(self, uri: URI, resource: Resource[D]):
        """
        Add the given `Resource` to the registry, without crawling it.
        """
        return self.with_resources([(uri, resource)])

    def with_resources(
        self,
        pairs: Iterable[tuple[URI, Resource[D]]],
    ) -> Registry[D]:
        r"""
        Add the given `Resource`\ s to the registry, without crawling them.
        """
        resources = self._resources.evolver()
        uncrawled = self._uncrawled.evolver()
        for uri, resource in pairs:
            uncrawled.add(uri)
            resources[uri] = resource
        return evolve(
            self,
            resources=resources.persistent(),
            uncrawled=uncrawled.persistent(),
        )

    def with_contents(
        self,
        pairs: Iterable[tuple[URI, D]],
        **kwargs: Any,
    ) -> Registry[D]:
        r"""
        Add the given contents to the registry, autodetecting when necessary.
        """
        return self.with_resources(
            (uri, Resource.from_contents(each, **kwargs))
            for uri, each in pairs
        )

    def combine(self, *registries: Registry[D]) -> Registry[D]:
        """
        Combine together one or more other registries, producing a unified one.
        """
        anchors = self._anchors
        resources = self._resources
        uncrawled = self._uncrawled
        retrieve = self._retrieve
        for registry in registries:
            anchors = anchors.update(registry._anchors)  # type: ignore[reportUnknownMemberType]  # noqa: E501
            resources = resources.update(registry._resources)  # type: ignore[reportUnknownMemberType]  # noqa: E501
            uncrawled = uncrawled.update(registry._uncrawled)  # type: ignore[reportUnknownMemberType]  # noqa: E501

            if registry._retrieve != _fail_to_retrieve:
                if registry._retrieve != retrieve != _fail_to_retrieve:
                    raise ValueError(
                        "Cannot combine registries with conflicting retrieval "
                        "functions.",
                    )
                retrieve = registry._retrieve
        return evolve(
            self,
            anchors=anchors,
            resources=resources,
            uncrawled=uncrawled,
            retrieve=retrieve,
        )

    def resolver(self, base_uri: URI = "") -> Resolver[D]:
        """
        Return a `Resolver` which resolves references against this registry.
        """
        return Resolver(base_uri=base_uri, registry=self)


@frozen
class Resolved(Generic[D]):
    """
    A resolved reference.
    """

    contents: D
    resolver: Resolver[D]


@frozen
class Resolver(Generic[D]):
    """
    A reference resolver.

    Resolvers help resolve references (including relative ones) by
    pairing a fixed base URI with a `Registry`.

    References are resolved against the base URI, and the combined URI
    is then looked up within the registry.

    The process of resolving a reference may itself involve calculating
    a *new* base URI for future reference resolution (e.g. if an
    intermediate resource sets a new base URI), or may involve encountering
    additional subresources and adding them to a new registry.
    """

    _base_uri: str = field(alias="base_uri")
    _registry: Registry[D] = field(alias="registry")
    _previous: PList[URI] = field(
        default=plist(),  # type: ignore[reportUnknownArgumentType]
        repr=False,
        alias="previous",
    )

    def lookup(self, ref: URI) -> Resolved[D]:
        """
        Resolve the given reference to the resource it points to.

        Raises:

            `exceptions.Unresolvable`

                or a subclass thereof (see below) if the reference isn't
                resolvable

            `exceptions.NoSuchAnchor`

                if the reference is to a URI where a resource exists but
                contains a plain name fragment which does not exist within
                the resource

            `exceptions.PointerToNowhere`

                if the reference is to a URI where a resource exists but
                contains a JSON pointer to a location within the resource
                that does not exist
        """
        if ref.startswith("#"):
            uri, fragment = self._base_uri, ref[1:]
        else:
            uri, fragment = urldefrag(urljoin(self._base_uri, ref))
        registry = self._registry
        resource = registry.get(uri)
        if resource is None:
            registry = registry.crawl()
            try:
                resource = registry[uri]
            except exceptions.NoSuchResource:
                raise exceptions.Unresolvable(ref=ref) from None
            except exceptions.Unretrievable:
                raise exceptions.Unresolvable(ref=ref)

        if fragment.startswith("/"):
            return resource.pointer(
                pointer=fragment,
                resolver=self._evolve(registry=registry, base_uri=uri),
            )

        if fragment:
            try:
                anchor = registry.anchor(uri, fragment)
            except LookupError:
                registry = registry.crawl()
                try:
                    anchor = registry.anchor(uri, fragment)
                except LookupError:
                    raise exceptions.NoSuchAnchor(
                        ref=ref,
                        resource=resource,
                        anchor=fragment,
                    )
            return anchor.resolve(
                resolver=self._evolve(registry=registry, base_uri=uri),
            )

        return Resolved(
            contents=resource.contents,
            resolver=self._evolve(registry=registry, base_uri=uri),
        )

    def in_subresource(self, subresource: Resource[D]) -> Resolver[D]:
        """
        Create a resolver for a subresource (which may have a new base URI).
        """
        id = subresource.id()
        if id is None:
            return self
        return self._evolve(base_uri=urljoin(self._base_uri, id))

    def dynamic_scope(self) -> Iterable[tuple[URI, Registry[D]]]:
        """
        In specs with such a notion, return the URIs in the dynamic scope.
        """
        for uri in self._previous:
            yield uri, self._registry

    def _evolve(self, base_uri: str, **kwargs: Any):
        """
        Evolve, appending to the dynamic scope.
        """
        previous = self._previous
        if self._base_uri and base_uri != self._base_uri:
            previous = previous.cons(self._base_uri)
        return evolve(self, base_uri=base_uri, previous=previous, **kwargs)


@frozen
class Anchor(Generic[D]):
    """
    A simple anchor in a `Resource`.
    """

    name: str
    resource: Resource[D]

    def resolve(self, resolver: Resolver[D]):
        """
        Return the resource for this anchor.
        """
        return Resolved(contents=self.resource.contents, resolver=resolver)
