from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from typing import Any, Callable, ClassVar, Generic
from urllib.parse import unquote, urldefrag, urljoin

from attrs import evolve, field
from pyrsistent import m, pmap
from pyrsistent.typing import PMap

from referencing._attrs import frozen
from referencing.exceptions import CannotDetermineSpecification, Unresolvable
from referencing.typing import URI, D, Mapping


@frozen
class Specification(Generic[D]):
    """
    A specification which defines referencing behavior.

    The various methods of a `Specification` allow for varying referencing
    behavior across JSON Schema specification versions, etc.
    """

    id_of: Callable[[D], URI | None]

    #: An opaque specification where resources have no subresources
    #: nor internal identifiers.
    OPAQUE: ClassVar[Specification[Any]]

    def create_resource(self, contents: D) -> Resource[D]:
        """
        Create a resource which is interpreted using this specification.
        """
        return Resource(contents=contents, specification=self)


Specification.OPAQUE = Specification(id_of=lambda contents: None)


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

        if specification is None:
            raise CannotDetermineSpecification(contents)
        return cls(contents=contents, specification=specification)  # type: ignore[reportUnknownArgumentType]  # noqa: E501

    @classmethod
    def opaque(cls, contents: D) -> Resource[D]:
        """
        Create an opaque `Resource` -- i.e. one with opaque specification.

        See `Specification.OPAQUE` for details.
        """
        return cls(contents=contents, specification=Specification.OPAQUE)

    def id(self) -> URI | None:
        """
        Retrieve this resource's (specification-specific) identifier.
        """
        return self._specification.id_of(self.contents)

    def pointer(self, pointer: str, resolver: Resolver[D]) -> Resolved[D]:
        """
        Resolve the given JSON pointer.
        """
        contents = self.contents
        for segment in unquote(pointer[1:]).split("/"):
            if isinstance(contents, Sequence):
                segment = int(segment)
            else:
                segment = segment.replace("~1", "/").replace("~0", "~")
            contents = contents[segment]  # type: ignore[reportUnknownArgumentType]  # noqa: E501
        return Resolved(contents=contents, resolver=resolver)  # type: ignore[reportUnknownArgumentType]  # noqa: E501


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
    """

    _contents: PMap[URI, Resource[D]] = field(default=m(), converter=pmap)  # type: ignore[reportUnknownArgumentType]  # noqa: E501

    def __getitem__(self, uri: URI) -> Resource[D]:
        """
        Return the `Resource` identified by the given URI.
        """
        return self._contents[uri]

    def __iter__(self) -> Iterator[URI]:
        """
        Iterate over all known URIs in the registry.
        """
        return iter(self._contents)

    def __len__(self) -> int:
        """
        Count the total number of (fully crawled) resources in this registry.
        """
        return len(self._contents)

    def contents(self, uri: URI) -> D:
        """
        Retrieve the contents identified by the given URI.
        """
        return self._contents[uri].contents

    def crawl(self) -> Registry[D]:
        """
        Immediately crawl all added resources, discovering subresources.
        """
        return self

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
        return evolve(self, contents=self._contents.update(pmap(pairs)))  # type: ignore[reportUnknownArgumentType]  # noqa: E501

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
        contents = (registry._contents for registry in registries)
        return evolve(self, contents=self._contents.update(*contents))  # type: ignore[reportUnknownMemberType]  # noqa: E501

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
    intermediate resource sets a new base URI).
    """

    _base_uri: str = field(alias="base_uri")
    _registry: Registry[D] = field(alias="registry")

    def lookup(self, ref: URI) -> Resolved[D]:
        """
        Resolve the given reference to the resource it points to.

        Raises:

            `Unresolvable`

                if the reference isn't resolvable
        """
        uri, fragment = urldefrag(urljoin(self._base_uri, ref))
        try:
            resource = self._registry[uri]
            if fragment.startswith("/"):
                return resource.pointer(pointer=fragment, resolver=self)
        except KeyError:
            raise Unresolvable(ref=ref) from None

        return Resolved(contents=resource.contents, resolver=self)
