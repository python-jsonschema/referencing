from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from urllib.parse import unquote, urldefrag, urljoin

from attrs import evolve, field
from pyrsistent import m, plist, pmap, s
from pyrsistent.typing import PList, PMap, PSet

from referencing._attrs import define, frozen
from referencing.typing import Anchor as AnchorType, ObjectSchema, Schema


class UnidentifiedResource(Exception):
    pass


@frozen
class IdentifiedResource:

    _specification: Specification
    resource: Schema

    @classmethod
    def from_resource(
        cls,
        resource: Schema,
        default_specification: Specification = ...,  # type: ignore
    ):
        specification = default_specification

        if resource is not True and resource is not False:
            jsonschema_schema_keyword = resource.get("$schema")
            if jsonschema_schema_keyword is not None:
                from referencing import jsonschema

                specification = jsonschema.BY_ID.get(
                    jsonschema_schema_keyword,
                    default_specification,
                )

        if specification is ...:
            raise UnidentifiedResource(resource)
        return cls(resource=resource, specification=specification)

    def pointer(self, base_uri: str, pointer: str) -> tuple[str, Schema]:
        """
        Resolve the given JSON pointer, returning a base URI and resource.
        """
        resource = self.resource
        for segment in unquote(pointer[1:]).split("/"):
            if isinstance(resource, Sequence):
                segment = int(segment)  # type: ignore
            else:
                segment = segment.replace("~1", "/").replace("~0", "~")
            resource = resource[segment]  # type: ignore # this can't be a bool
            # FIXME: this is wrong, we need to know that we are crossing
            #        the boundary of a *schema* specifically
            if not isinstance(resource, Sequence):
                id = self._specification.id_of(resource)
                if id is not None:
                    base_uri = urljoin(base_uri, id)
        return base_uri, resource

    def id(self):
        return self._specification.id_of(self.resource)

    def anchors(self) -> Iterable[AnchorType]:
        if isinstance(self.resource, bool):
            return []
        return self._specification.anchors_in(self.resource)

    def subresources(self) -> Iterable[IdentifiedResource]:
        subresources = self._specification.subresources_of(self.resource)  # type: ignore  # FIXME: missing test  # noqa: E501
        return (
            IdentifiedResource.from_resource(
                resource=each,
                default_specification=self._specification,
            )
            for each in subresources
            if each is not True and each is not False
        )


@frozen
class Anchor:

    name: str
    resource: IdentifiedResource

    def resolve(self, resolver, uri):
        return self.resource, uri


@frozen
class Specification:
    """
    A referencing-defining specification.

    See `referencing.jsonschema` for JSON Schema-specific instances.
    """

    id_of: Callable[[Schema], str | None]
    subresources_of: Callable[[ObjectSchema], Iterable[Schema]]
    _anchors_in: Callable[[ObjectSchema, Specification], Iterable[AnchorType]]

    def anchors_in(self, resource: ObjectSchema) -> Iterable[AnchorType]:
        return self._anchors_in(resource, self)


#: A 'null' specification, where resources are opaque
#: (e.g. have no subresources or IDs).
OPAQUE_SPECIFICATION = Specification(
    id_of=lambda resource: None,
    anchors_in=lambda resource, specification: [],
    subresources_of=lambda resource: (),
)


@frozen
class Registry:

    _contents: PMap[
        str,
        tuple[IdentifiedResource, PMap[str, AnchorType]],
    ] = field(
        default=m(),
        repr=lambda value: f"({len(value)} entries)",
    )
    _uncrawled: PSet[str] = field(default=s(), repr=False)

    def update(self, *registries: Registry) -> Registry:
        contents = (each._contents for each in registries)
        uncrawled = (each._uncrawled for each in registries)
        return evolve(
            self,
            contents=self._contents.update(*contents),
            uncrawled=self._uncrawled.update(*uncrawled),
        )

    def with_resource(self, resource: Schema) -> Registry:
        identified = IdentifiedResource.from_resource(resource)
        return self.with_identified_resource(
            uri=identified.id(),
            resource=identified,
        )

    def with_resources(
        self,
        pairs: Iterable[tuple[str, Schema]],
        **kwargs,
    ) -> Registry:
        return self.with_identified_resources(
            (uri, IdentifiedResource.from_resource(resource, **kwargs))
            for uri, resource in pairs
        )

    def with_identified_resource(
        self,
        uri: str,
        resource: IdentifiedResource,
    ) -> Registry:
        return self.with_identified_resources([(uri, resource)])

    def with_identified_resources(
        self,
        pairs: Iterable[tuple[str, IdentifiedResource]],
    ) -> Registry:
        uncrawled = self._uncrawled.evolver()
        contents = self._contents.evolver()
        for uri, resource in pairs:
            if uri not in self._contents or self._contents[uri][0] != resource:
                uncrawled.add(uri)
            contents[uri] = resource, m()
        return evolve(
            self,
            contents=contents.persistent(),
            uncrawled=uncrawled.persistent(),
        )

    def resource_at(
        self,
        uri: str,
    ) -> tuple[IdentifiedResource, PMap[str, AnchorType], Registry]:
        at_uri = self._contents.get(uri)
        if at_uri is None or uri in self._uncrawled:
            registry = self._crawl()
            return *registry._contents[uri], registry
        return *at_uri, self

    def _crawl(self) -> Registry:
        contents = self._contents.evolver()
        resources = [(uri, contents[uri][0]) for uri in self._uncrawled]
        while resources:
            uri, resource = resources.pop()
            anchors = pmap((each.name, each) for each in resource.anchors())

            id = resource.id()
            if id is None:
                if anchors:
                    old, old_anchors = contents[uri]
                    contents[uri] = old, old_anchors.update(anchors)
            else:
                uri = urljoin(uri, id)
                contents[uri] = resource, anchors

            resources.extend((uri, each) for each in resource.subresources())
        return evolve(self, contents=contents.persistent(), uncrawled=s())

    def resolver(self, root: Schema, specification: Specification) -> Resolver:
        uri = specification.id_of(root) or ""
        registry = self.with_identified_resource(
            uri=uri,
            resource=IdentifiedResource(
                resource=root,
                specification=specification,
            ),
        )
        return Resolver(base_uri=uri, registry=registry)


@define
class Resolver:

    _base_uri: str
    _registry: Registry
    _previous: PList[str] = field(default=plist(), repr=False)

    def lookup(self, ref: str) -> tuple[Schema, Resolver]:
        if ref.startswith("#"):
            uri, fragment = self._base_uri, ref[1:]
        else:
            uri, fragment = urldefrag(urljoin(self._base_uri, ref))

        resource, anchors, registry = self._registry.resource_at(uri)

        if fragment.startswith("/"):
            base_uri, target = resource.pointer(base_uri=uri, pointer=fragment)
        else:
            if fragment:
                resource, uri = anchors[fragment].resolve(
                    resolver=self,
                    uri=uri,
                )

            base_uri, target = uri, resource.resource
            id = resource.id()
            if id is not None:
                base_uri = urljoin(self._base_uri, id).rstrip("#")
        return target, self._evolve(base_uri=base_uri, registry=registry)

    def with_root(
        self,
        root: Schema,
        specification: Specification,
    ) -> Resolver:
        maybe_relative = specification.id_of(root)
        if maybe_relative is None:
            return self

        uri = urljoin(self._base_uri, maybe_relative)
        registry = self._registry.with_identified_resource(
            uri=uri,
            resource=IdentifiedResource(
                resource=root,
                specification=specification,
            ),
        )
        return self._evolve(base_uri=uri, registry=registry)

    def dynamic_scope(
        self,
    ) -> Iterable[tuple[str, IdentifiedResource, PMap[str, AnchorType]]]:
        for uri in self._previous:
            resource, anchors, _ = self._registry.resource_at(uri)
            yield uri, resource, anchors

    def _evolve(self, **kwargs):
        previous = self._previous.cons(self._base_uri)
        return evolve(self, previous=previous, **kwargs)
