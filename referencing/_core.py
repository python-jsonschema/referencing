from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any, Callable, ClassVar, Generic

from attrs import evolve, field
from pyrsistent import m, pmap
from pyrsistent.typing import PMap

from referencing._attrs import frozen
from referencing.exceptions import CannotDetermineSpecification
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
        default_specification: Specification[D] = ...,
    ) -> Resource[D]:
        """
        Attempt to discern which specification applies to the given contents.
        """
        specification = default_specification
        if isinstance(contents, Mapping):
            jsonschema_dialect_id = contents.get("$schema")  # type: ignore[reportUnknownMemberType]  # noqa: E501
            if jsonschema_dialect_id is not None:
                from referencing.jsonschema import specification_with

                specification = specification_with(jsonschema_dialect_id)  # type: ignore[reportUnknownArgumentType]  # noqa: E501

        if specification is ...:
            raise CannotDetermineSpecification(contents)
        return cls(contents=contents, specification=specification)  # type: ignore[reportUnknownArgumentType]  # noqa: E501

    def id(self) -> URI | None:
        """
        Retrieve this resource's (specification-specific) identifier.
        """
        return self._specification.id_of(self.contents)


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

    _contents: PMap[URI, Resource[D]] = m()

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
        Count the total number of (fully crawled) resources  in this registry.
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
