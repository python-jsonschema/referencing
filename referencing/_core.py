from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Callable, ClassVar, Generic

from attrs import evolve
from pyrsistent import pmap
from pyrsistent.typing import PMap

from referencing._attrs import frozen
from referencing.typing import URI, D


@frozen
class CannotDetermineSpecification(Exception):
    """
    Attempting to detect the appropriate `Specification` failed.

    This happens if no discernible information is found in the contents of the
    new resource which would help identify it.
    """

    contents: Any


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
    _specification: Specification[D]

    @classmethod
    def from_contents(
        cls,
        contents: D,
        default_specification: Specification[D] = ...,  # type: ignore[assignment]  # noqa: E501
    ) -> Resource[D]:
        """
        Attempt to discern which specification applies to the given contents.
        """
        specification = default_specification
        if isinstance(contents, Mapping):
            jsonschema_dialect_identifier = contents.get("$schema")
            if jsonschema_dialect_identifier is not None:
                from referencing import jsonschema

                specification = jsonschema.BY_ID[jsonschema_dialect_identifier]

        if specification is ...:  # type: ignore[comparison-overlap]
            raise CannotDetermineSpecification(contents)
        return cls(contents=contents, specification=specification)

    def id(self) -> URI | None:
        """
        Retrieve this resource's (specification-specific) identifier.
        """
        return self._specification.id_of(self.contents)


@frozen
class Registry(Generic[D]):
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

    _contents: PMap[URI, Resource[D]] = pmap()

    def __getitem__(self, uri: URI) -> Resource[D]:
        """
        Return the `Resource` identified by the given URI.
        """
        return self._contents[uri]

    def contents(self, uri: URI) -> D:
        """
        Retreive the contents identified by the given URI.
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
        return evolve(self, contents=self._contents.update(pmap(pairs)))
